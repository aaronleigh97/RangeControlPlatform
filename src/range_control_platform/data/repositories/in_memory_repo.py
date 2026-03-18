from range_control_platform.data.seed import seed_reference_data


class InMemoryReferenceDataRepository:
    def load_reference_data(self) -> dict:
        return seed_reference_data()
