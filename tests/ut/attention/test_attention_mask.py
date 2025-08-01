#
# Copyright (c) 2025 Huawei Technologies Co., Ltd. All Rights Reserved.
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

import torch

from tests.ut.base import TestBase
from vllm_ascend.attention.attention_mask import AttentionMaskBuilder


class TestAttentionMaskBuilder(TestBase):

    def test_init_attention_mask_builder(self):
        # generate attention_mask_builder with float16
        attention_mask_builder = AttentionMaskBuilder(max_seq_len=1024,
                                                      dtype=torch.float16)
        self.assertEqual(attention_mask_builder._seq_len_cached, 1024)
        self.assertEqual(attention_mask_builder.attn_mask_cache.dtype,
                         torch.float16)
        self.assertEqual(attention_mask_builder.splitfuse_mask_value, -10000)
        self.assertEqual(attention_mask_builder.attn_mask_cache.shape,
                         (1024, 1024))
        self.assertEqual(attention_mask_builder.attn_mask_cache[0][-1],
                         torch.tensor(float("-inf"), dtype=torch.float16))

        # generate attention_mask_builder with int8
        attention_mask_builder = AttentionMaskBuilder(max_seq_len=512,
                                                      dtype=torch.int8)
        self.assertEqual(attention_mask_builder._seq_len_cached, 512)
        self.assertEqual(attention_mask_builder.attn_mask_cache.dtype,
                         torch.int8)
        self.assertEqual(attention_mask_builder.splitfuse_mask_value, -10000)
        self.assertEqual(attention_mask_builder.attn_mask_cache.shape,
                         (512, 512))
        self.assertEqual(attention_mask_builder.attn_mask_cache[0][-1],
                         torch.tensor(1, dtype=torch.int8))

    def test_get_attn_mask(self):
        # if the len is less than max_seq_len, the attn_mask_cache will not be updated
        attention_mask_builder = AttentionMaskBuilder(max_seq_len=1024,
                                                      dtype=torch.float16)
        attn_mask = attention_mask_builder.get_attn_mask(
            max_seq_len=512, dtype=torch.float16, device=torch.device("cpu"))
        self.assertEqual(attn_mask.shape, (512, 512))
        self.assertEqual(attn_mask[0][-1],
                         torch.tensor(float("-inf"), dtype=torch.float16))
        self.assertEqual(attention_mask_builder._seq_len_cached, 1024)
        self.assertEqual(attention_mask_builder.attn_mask_cache.shape,
                         (1024, 1024))
        self.assertEqual(attention_mask_builder.attn_mask_cache[0][-1],
                         torch.tensor(float("-inf"), dtype=torch.float16))

        # if the len is greater than max_seq_len, the attn_mask_cache will be updated
        attn_mask = attention_mask_builder.get_attn_mask(
            max_seq_len=2048, dtype=torch.float16, device=torch.device("cpu"))
        self.assertEqual(attn_mask.shape, (2048, 2048))
        self.assertEqual(attn_mask[0][-1],
                         torch.tensor(float("-inf"), dtype=torch.float16))
        self.assertEqual(attention_mask_builder._seq_len_cached, 2048)
        self.assertEqual(attention_mask_builder.attn_mask_cache.shape,
                         (2048, 2048))
        self.assertEqual(attention_mask_builder.attn_mask_cache[0][-1],
                         torch.tensor(float("-inf"), dtype=torch.float16))

    def test_get_splitfuse_attn_mask(self):
        attention_mask_builder = AttentionMaskBuilder(max_seq_len=1024,
                                                      dtype=torch.float16)
        attn_mask = attention_mask_builder.get_splitfuse_attn_mask(
            seq_lens=[512],
            query_lens=[512],
            position=torch.tensor([0]),
            dtype=torch.float16,
            device=torch.device("cpu"),
        )
        self.assertEqual(attn_mask.shape, (1, 512))
        self.assertEqual(attention_mask_builder._seq_len_cached, 1024)

        attn_mask = attention_mask_builder.get_splitfuse_attn_mask(
            seq_lens=[2048],
            query_lens=[1024],
            position=torch.tensor([0]),
            dtype=torch.float16,
            device=torch.device("cpu"),
        )
        self.assertEqual(attn_mask.shape, (1024, 2048))

        attention_mask_builder = AttentionMaskBuilder(max_seq_len=1024,
                                                      dtype=torch.int8)
        attn_mask = attention_mask_builder.get_splitfuse_attn_mask(
            seq_lens=[512],
            query_lens=[512],
            position=torch.tensor([0]),
            dtype=torch.int8,
            device=torch.device("cpu"),
        )
        self.assertEqual(attn_mask.shape, (1, 512))
