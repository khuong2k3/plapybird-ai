from collections.abc import Iterator
from dataclasses import dataclass
import io
import torch as tch
import torch.nn.functional as F


@dataclass
class AIBase:
    w1: tch.Tensor
    b1: tch.Tensor
    w2: tch.Tensor
    b2: tch.Tensor

    def __init__(self) -> None:
        self.w1 = tch.zeros((5, 3), dtype=tch.float32)
        self.b1 = tch.zeros(5, dtype=tch.float32)
        self.w2 = tch.zeros((2, 5), dtype=tch.float32)
        self.b2 = tch.zeros(2, dtype=tch.float32)

    def save(self, filename = "ai.tch"):
        tch.save(
            {
                "w1": self.w1,
                "w2": self.w2,
                "b1": self.b1,
                "b2": self.b2,
            },
            filename,
        )

    def load(filename = "ai.tch"):
        ai = AIBase()
        load_obj = tch.load(filename)
        ai.w1 = load_obj["w1"]
        ai.w2 = load_obj["w2"]
        ai.b1 = load_obj["b1"]
        ai.b2 = load_obj["b2"]
        return ai

    def forward(self, input: tch.Tensor):
        x = self.w1.matmul(input) + self.b1
        x = F.relu(x)
        return self.w2.matmul(x) + self.b2

    def tweak(self, lr: float = 0.01):
        ai = AIBase()
        ai.w1 = self.w1 + lr * 2.0 * tch.rand(self.w1.shape) - lr
        ai.w2 = self.w2 + lr * 2.0 * tch.rand(self.w2.shape) - lr
        ai.b1 = self.b1 + lr * 2.0 * tch.rand(self.b1.shape) - lr
        ai.b2 = self.b2 + lr * 2.0 * tch.rand(self.b2.shape) - lr
        return ai


class AIFactory:
    best_ai: AIBase

    def __init__(self, prev_best: str = "ai.tch") -> None:
        try:
            save_file = open(prev_best, "rb")
            file_like = io.BytesIO(save_file.read())
            self.best_ai: AIBase = AIBase.load(file_like)
        except:
            self.best_ai: AIBase = AIBase()

    def set_best(self, ai: AIBase):
        self.best_ai = ai

    def generate(self, num: int, lr: float = 0.01) -> Iterator[AIBase]:
        yield self.best_ai
        current_gen = self.best_ai
        for _ in range(num):
            new_gen = current_gen.tweak(lr)
            current_gen = new_gen
            yield new_gen
