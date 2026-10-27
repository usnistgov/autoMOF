from unitelabs.cdk import sila

class SimpleReturnYes2(sila.Feature):
    """
    Function to test client usage
    """
    def __init__(self, name= "Simple Return Yes 2") -> None:
        super().__init__(
            name= name,
            originator="io.unitelabs",
            category="test",
        )
        self.active_config = {"A": "a value", "B": "b value"}

    @sila.UnobservableProperty()
    async def get_yes(self) -> str:
        return "Yes"

    @sila.ObservableCommand()
    async def iterative_method(
        self,
        seed: int,
        iterations: int,
        *,
        status: sila.Status,
        intermediate: sila.Intermediate[int],
    ) -> float:
        """
        Create a random number based on a `seed` after `iterations`.

        Args:
          Seed: Number used to initialize the pseudorandom number generator.
          NumberOfIterations: How many times to iterate before number generation.

        Yields:
          CurrentIteration: The current iteration.

        Returns:
          RandomNumber: A random number.
        """

        import asyncio
        import random

        random.seed(seed)

        total = iterations + 1
        for x in range(1, total):
            intermediate.send(x)
            status.update(progress=(x / total))
            await asyncio.sleep(1)

        return random.random()

