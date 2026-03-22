from range_control_platform.data.seed import seed_reference_data


class JDBigQueryReferenceDataRepository:
    _STORES_QUERY = """
    SELECT
      CAST(branch_id AS STRING) AS branch_id,
      branch_name,
      fascia,
      status,
      square_footage,
      budget_2026,
      store_grade,
      region,
      fit_type,
      indoor_tent_field_sqft,
      outdoor_tent_field_sqft
    FROM `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stores`
    ORDER BY fascia, branch_name
    """

    _DEPARTMENT_GRADE_ALLOCATIONS_QUERY = """
    SELECT
      department_name,
      grade,
      allowed_linear_meterage
    FROM `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.department_grade_allocations`
    ORDER BY department_name, grade
    """

    _STAND_LIBRARY_QUERY = """
    SELECT
      stand_id,
      stand_name,
      stand_type,
      stand_height,
      arms,
      sqm
    FROM `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stand_library`
    ORDER BY stand_id
    """

    _PRODUCT_RANGE_QUERY = """
    SELECT
      CAST(product_id AS STRING) AS product_id,
      CAST(product_code AS STRING) AS product_code,
      product_name,
      department_name,
      range_name
    FROM `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.product_range_master`
    WHERE department_name IS NOT NULL
    ORDER BY department_name, range_name, product_name, product_code
    """

    @staticmethod
    def _clean_text(value):
        text = str(value or "").strip()
        return text or None

    def load_reference_data(self) -> dict:
        try:
            from deploy_frameworks.bigquery import bigquery
        except ImportError as exc:
            raise RuntimeError(
                "deploy_frameworks.bigquery is not installed or unavailable. "
                "Install the JD frameworks package or switch ENV back to 'local'."
            ) from exc

        reference_data = seed_reference_data()

        stores_rows = bigquery(self._STORES_QUERY).to_dict("records")
        allocation_rows = bigquery(self._DEPARTMENT_GRADE_ALLOCATIONS_QUERY).to_dict("records")
        stand_rows = bigquery(self._STAND_LIBRARY_QUERY).to_dict("records")
        try:
            product_rows = bigquery(self._PRODUCT_RANGE_QUERY).to_dict("records")
        except Exception:
            product_rows = reference_data.get("products", [])

        open_stores = []
        facias = set()
        grades = set()
        departments = set()
        branches = []
        department_grade_allocations = []
        stand_library = []
        products = []

        for row in stores_rows:
            branch_id = self._clean_text(row.get("branch_id"))
            branch_name = self._clean_text(row.get("branch_name"))
            fascia = self._clean_text(row.get("fascia"))
            status = self._clean_text(row.get("status"))
            grade = self._clean_text(row.get("store_grade"))

            if not branch_id:
                continue

            store = {
                "branch_id": branch_id,
                "branch_name": branch_name or branch_id,
                "fascia": fascia,
                "status": status,
                "square_footage": row.get("square_footage"),
                "budget_2026": row.get("budget_2026"),
                "store_grade": grade,
                "region": self._clean_text(row.get("region")),
                "fit_type": self._clean_text(row.get("fit_type")),
                "indoor_tent_field_sqft": row.get("indoor_tent_field_sqft"),
                "outdoor_tent_field_sqft": row.get("outdoor_tent_field_sqft"),
            }
            open_stores.append(store)

            if status != "Open":
                continue

            if fascia:
                facias.add(fascia)
            if grade:
                grades.add(grade)

            branch_label = branch_name or branch_id
            branches.append(
                {
                    "branch_id": branch_id,
                    "branch_name": branch_name or branch_id,
                    "branch_label": f"{branch_id} - {branch_label}" if branch_name else branch_id,
                    "grade": grade,
                    "facia": fascia,
                    "status": status,
                    "square_footage": row.get("square_footage"),
                    "budget_2026": row.get("budget_2026"),
                    "region": self._clean_text(row.get("region")),
                    "fit_type": self._clean_text(row.get("fit_type")),
                }
            )

        for row in allocation_rows:
            department_name = self._clean_text(row.get("department_name"))
            grade = self._clean_text(row.get("grade"))
            allowed_linear_meterage = row.get("allowed_linear_meterage")

            if not (department_name and grade and allowed_linear_meterage is not None):
                continue

            departments.add(department_name)
            grades.add(grade)
            department_grade_allocations.append(
                {
                    "department_name": department_name,
                    "grade": grade,
                    "allowed_linear_meterage": allowed_linear_meterage,
                }
            )

        for row in stand_rows:
            stand_id = self._clean_text(row.get("stand_id"))
            stand_name = self._clean_text(row.get("stand_name"))
            sqm = row.get("sqm")

            if not (stand_id and stand_name and sqm is not None):
                continue

            stand_library.append(
                {
                    "stand_id": stand_id,
                    "stand_name": stand_name,
                    "stand_type": self._clean_text(row.get("stand_type")),
                    "stand_height": self._clean_text(row.get("stand_height")),
                    "arms": row.get("arms"),
                    "sqm": sqm,
                }
            )

        for row in product_rows:
            product_id = self._clean_text(row.get("product_id"))
            product_code = self._clean_text(row.get("product_code"))
            product_name = self._clean_text(row.get("product_name"))
            department_name = self._clean_text(row.get("department_name"))

            if not (product_id and product_name and department_name):
                continue

            departments.add(department_name)
            products.append(
                {
                    "product_id": product_id,
                    "product_code": product_code or product_id,
                    "product_name": product_name,
                    "department_name": department_name,
                    "range_name": self._clean_text(row.get("range_name")),
                }
            )

        reference_data["facias"] = sorted(facias)
        reference_data["grades"] = sorted(grades)
        reference_data["departments"] = sorted(departments)
        reference_data["branches"] = branches
        reference_data["stores"] = open_stores
        reference_data["department_grade_allocations"] = department_grade_allocations
        reference_data["stand_library"] = stand_library
        reference_data["products"] = products
        return reference_data
