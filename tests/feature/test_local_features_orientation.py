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

from kornia.feature.orientation import LAFOrienter, OriNet, PassLAF, PatchDominantGradientOrientation
from kornia.geometry.conversions import rad2deg

from testing.base import BaseTester


class TestPassLAF(BaseTester):
    def test_shape(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        laf = torch.rand(1, 1, 2, 3, device=device)
        ori = PassLAF().to(device)
        out = ori(laf, inp)
        assert out.shape == laf.shape

    def test_shape_batch(self, device):
        inp = torch.rand(2, 1, 32, 32, device=device)
        laf = torch.rand(2, 34, 2, 3, device=device)
        ori = PassLAF().to(device)
        out = ori(laf, inp)
        assert out.shape == laf.shape

    def test_print(self, device):
        sift = PassLAF()
        sift.__repr__()

    def test_pass(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        laf = torch.rand(1, 1, 2, 3, device=device)
        ori = PassLAF().to(device)
        out = ori(laf, inp)
        self.assert_close(out, laf)

    def test_gradcheck(self, device):
        batch_size, channels, height, width = 1, 1, 21, 21
        patches = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        laf = torch.rand(batch_size, 4, 2, 3, device=device, dtype=torch.float64)
        self.gradcheck(PassLAF().to(device), (patches, laf))


class TestPatchDominantGradientOrientation(BaseTester):
    def test_shape(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        ori = PatchDominantGradientOrientation(32).to(device)
        ang = ori(inp)
        assert ang.shape == torch.Size([1])

    def test_shape_batch(self, device):
        inp = torch.rand(10, 1, 32, 32, device=device)
        ori = PatchDominantGradientOrientation(32).to(device)
        ang = ori(inp)
        assert ang.shape == torch.Size([10])

    def test_print(self, device):
        sift = PatchDominantGradientOrientation(32)
        sift.__repr__()

    def test_toy(self, device):
        ori = PatchDominantGradientOrientation(19).to(device)
        inp = torch.zeros(1, 1, 19, 19, device=device)
        inp[:, :, :10, :] = 1
        ang = ori(inp)
        expected = torch.tensor([90.0], device=device)
        self.assert_close(rad2deg(ang), expected)

    def test_gradcheck(self, device):
        batch_size, channels, height, width = 1, 1, 13, 13
        ori = PatchDominantGradientOrientation(width).to(device)
        patches = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        self.gradcheck(ori, (patches,))

    @pytest.mark.jit()
    @pytest.mark.skip(" Compiled functions can't take variable number")
    def test_jit(self, device, dtype):
        B, C, H, W = 2, 1, 13, 13
        patches = torch.ones(B, C, H, W, device=device, dtype=dtype)
        model = PatchDominantGradientOrientation(13).to(patches.device, patches.dtype).eval()
        model_jit = torch.jit.script(PatchDominantGradientOrientation(13).to(patches.device, patches.dtype).eval())
        self.assert_close(model(patches), model_jit(patches))


class TestOriNet(BaseTester):
    def test_shape(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        ori = OriNet().to(device=device, dtype=inp.dtype).eval()
        ang = ori(inp)
        assert ang.shape == torch.Size([1])

    def test_pretrained(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        ori = OriNet(True).to(device=device, dtype=inp.dtype).eval()
        ang = ori(inp)
        assert ang.shape == torch.Size([1])

    def test_shape_batch(self, device):
        inp = torch.rand(2, 1, 32, 32, device=device)
        ori = OriNet(True).to(device=device, dtype=inp.dtype).eval()
        ang = ori(inp)
        assert ang.shape == torch.Size([2])

    def test_print(self, device):
        sift = OriNet(32)
        sift.__repr__()

    def test_toy(self, device):
        inp = torch.zeros(1, 1, 32, 32, device=device)
        inp[:, :, :16, :] = 1
        ori = OriNet(True).to(device=device, dtype=inp.dtype).eval()
        ang = ori(inp)
        expected = torch.tensor([70.58], device=device)
        self.assert_close(rad2deg(ang), expected, atol=1e-2, rtol=1e-3)

    @pytest.mark.skip("jacobian not well computed")
    def test_gradcheck(self, device):
        batch_size, channels, height, width = 2, 1, 32, 32
        patches = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        ori = OriNet().to(device=device, dtype=patches.dtype)
        self.gradcheck(ori, (patches,), fast_mode=False)

    @pytest.mark.jit()
    def test_jit(self, device, dtype):
        B, C, H, W = 2, 1, 32, 32
        patches = torch.ones(B, C, H, W, device=device, dtype=dtype)
        tfeat = OriNet(True).to(patches.device, patches.dtype).eval()
        tfeat_jit = torch.jit.script(OriNet(True).to(patches.device, patches.dtype).eval())
        self.assert_close(tfeat_jit(patches), tfeat(patches))


class TestLAFOrienter(BaseTester):
    def test_shape(self, device):
        inp = torch.rand(1, 1, 32, 32, device=device)
        laf = torch.rand(1, 1, 2, 3, device=device)
        ori = LAFOrienter().to(device)
        out = ori(laf, inp)
        assert out.shape == laf.shape

    def test_shape_batch(self, device):
        inp = torch.rand(2, 1, 32, 32, device=device)
        laf = torch.rand(2, 34, 2, 3, device=device)
        ori = LAFOrienter().to(device)
        out = ori(laf, inp)
        assert out.shape == laf.shape

    def test_print(self, device):
        sift = LAFOrienter()
        sift.__repr__()

    def test_toy(self, device):
        ori = LAFOrienter(32).to(device)
        inp = torch.zeros(1, 1, 19, 19, device=device)
        inp[:, :, :, :10] = 1
        laf = torch.tensor([[[[5.0, 0.0, 8.0], [0.0, 5.0, 8.0]]]], device=device)
        new_laf = ori(laf, inp)
        expected = torch.tensor([[[[-5.0, 0.0, 8.0], [0.0, -5.0, 8.0]]]], device=device)
        self.assert_close(new_laf, expected)

    def test_gradcheck(self, device):
        batch_size, channels, height, width = 1, 1, 21, 21
        patches = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        laf = torch.ones(batch_size, 2, 2, 3, device=device, dtype=torch.float64)
        laf[:, :, 0, 1] = 0
        laf[:, :, 1, 0] = 0
        self.gradcheck(LAFOrienter(8).to(device), (laf, patches), rtol=1e-3, atol=1e-3)
