from datasets import load_dataset


class LMSYSLoader:
    """Utility to load and stream the LMSYS-Chat-1M dataset."""

    def __init__(self, dataset_name="OpenAssistant/oasst1"):
        self.dataset_name = dataset_name

    def load(self, split="train", stream=True):
        """Loads the dataset."""
        print(f"Loading dataset {self.dataset_name}...")
        return load_dataset(self.dataset_name, split=split, streaming=stream)

    def get_sample_conversations(self, n=5):
        """Returns n sample conversations from the dataset."""
        ds = self.load()
        samples = []
        for i, example in enumerate(ds):
            if i >= n:
                break
            samples.append(example)
        return samples
