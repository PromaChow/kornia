# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright 2018 Kornia Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest
import torch

from kornia.contrib.models.sam import Sam, SamConfig
from kornia.core import pad

from testing.base import BaseTester


def _pad_rb(x, size):
    """Pads right bottom."""
    pad_h = size - x.shape[-2]
    pad_w = size - x.shape[-1]
    return pad(x, (0, pad_w, 0, pad_h))


class TestSam(BaseTester):
    @pytest.mark.slow
    @pytest.mark.parametrize("model_type", ["vit_b", "mobile_sam"])
    def test_smoke(self, device, model_type):
        model = Sam.from_config(SamConfig(model_type)).to(device)
        assert isinstance(model, Sam)

        img_size = model.image_encoder.img_size
        data = torch.randn(1, 3, img_size, img_size, device=device)
        keypoints = torch.randint(0, img_size, (1, 2, 2), device=device, dtype=torch.float)
        labels = torch.randint(0, 1, (1, 2), device=device, dtype=torch.float)

        model(data, [{"points": (keypoints, labels)}], False)

    @pytest.mark.slow
    @pytest.mark.parametrize("batch_size", [1, 3])
    @pytest.mark.parametrize("N", [2, 5])
    @pytest.mark.parametrize("multimask_output", [True, False])
    def test_cardinality(self, device, batch_size, N, multimask_output):
        # SAM: don't supports float64
        dtype = torch.float32
        data = torch.rand(1, 3, 77, 128, device=device, dtype=dtype)
        model = Sam.from_config(SamConfig("vit_b"))
        model = model.to(device=device, dtype=dtype)
        data = _pad_rb(data, model.image_encoder.img_size)
        keypoints = torch.randint(0, min(data.shape[-2:]), (batch_size, N, 2), device=device).to(dtype=dtype)
        labels = torch.randint(0, 1, (batch_size, N), device=device).to(dtype=dtype)

        out = model(data, [{"points": (keypoints, labels)}], multimask_output)

        C = 3 if multimask_output else 1
        assert len(out) == data.size(0)
        assert out[0].logits.shape == (batch_size, C, 256, 256)

    def test_exception(self):
        model = Sam.from_config(SamConfig("mobile_sam"))

        with pytest.raises(TypeError) as errinfo:
            data = torch.rand(3, 1, 2)
            model(data, [], False)
        assert "shape must be [['B', '3', 'H', 'W']]. Got torch.Size([3, 1, 2])" in str(errinfo)

        with pytest.raises(Exception) as errinfo:
            data = torch.rand(2, 3, 1, 2)
            model(data, [{}], False)
        assert "The number of images (`B`) should match with the length of prompts!" in str(errinfo)

    @pytest.mark.slow
    @pytest.mark.parametrize("model_type", ["vit_b", "vit_l", "vit_h", "mobile_sam"])
    def test_config(self, device, model_type):
        model = Sam.from_config(SamConfig(model_type))
        model = model.to(device=device)

        assert isinstance(model, Sam)
        assert next(model.parameters()).device == device

    @pytest.mark.skip(reason="Unsupported at moment -- the code is not tested for training and had `torch.no_grad`")
    def test_gradcheck(self, device): ...

    @pytest.mark.skip(reason="Unnecessary test")
    def test_module(self): ...

    @pytest.mark.skip(reason="Needs to be reviewed.")
    def test_dynamo(self, device, torch_optimizer):
        dtype = torch.float32
        img = torch.rand(1, 3, 128, 75, device=device, dtype=dtype)

        op = Sam.from_config(SamConfig("vit_b"))
        op = op.to(device=device, dtype=dtype)

        op_optimized = torch_optimizer(op)

        img = _pad_rb(img, op.image_encoder.img_size)

        expected = op(img, [{}], False)
        actual = op_optimized(img, [{}], False)

        self.assert_close(expected[0].logits, actual[0].logits)
        self.assert_close(expected[0].scores, actual[0].scores)

    @pytest.mark.slow
    @pytest.mark.parametrize("model_type", ["vit_b", "mobile_sam"])
    def test_pretrained(self, model_type):
        Sam.from_config(SamConfig(model_type, pretrained=True))
