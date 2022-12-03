# -*- coding: utf-8 -*-
"""resnetSSD.ipynb
This code referred from torchvision SSD code (https://github.com/pytorch/vision/blob/main/torchvision/models/detection/ssd.py ) 
and NVIDIA model code(https://github.com/NVIDIA/DeepLearningExamples/blob/master/PyTorch/Detection/SSD/ssd/model.py ))

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PC09LpkWLkgf2SDl2TL0rayQbPcwNvpJ
"""

import torch
from torch import nn
from torchvision.models.resnet import resnet18, resnet34, resnet50, resnet101, resnet152
from collections import OrderedDict

class ResNet(nn.Module):
    def __init__(self, backbone='resnet50', backbone_path=None):
        super().__init__()
        if backbone == 'resnet18':
            backbone = resnet18(pretrained=not backbone_path)
            self.out_channels = [256, 512, 512, 256, 256, 128]
        elif backbone == 'resnet34':
            backbone = resnet34(pretrained=not backbone_path)
            self.out_channels = [256, 512, 512, 256, 256, 256]
        elif backbone == 'resnet50':
            backbone = resnet50(pretrained=not backbone_path)
            self.out_channels = [1024, 512, 512, 256, 256, 256]
        elif backbone == 'resnet101':
            backbone = resnet101(pretrained=not backbone_path)
            self.out_channels = [1024, 512, 512, 256, 256, 256]
        else:  # backbone == 'resnet152':
            backbone = resnet152(pretrained=not backbone_path)
            self.out_channels = [1024, 512, 512, 256, 256, 256]
        if backbone_path:
            backbone.load_state_dict(torch.load(backbone_path))


        self.feature_extractor = nn.Sequential(*list(backbone.children())[:7])

        conv4_block1 = self.feature_extractor[-1][0]

        conv4_block1.conv1.stride = (1, 1)
        conv4_block1.conv2.stride = (1, 1)
        conv4_block1.downsample[0].stride = (1, 1)

    def forward(self, x):
        x = self.feature_extractor(x)
        return x

#
#
class SSDFeatureExtractorRES(nn.Module):
    def __init__(self, backbone: nn.Module):
        super().__init__()

        self.feature_extractor = backbone

        self.label_num = 2  # number of COCO classes
        self._build_additional_features(self.feature_extractor.out_channels)
        self.num_defaults = [4, 6, 6, 6, 4, 4]

        
    def _build_additional_features(self, input_size):
        self.additional_blocks = []
        for i, (input_size, output_size, channels) in enumerate(zip(input_size[:-1], input_size[1:], [256, 256, 128, 128, 128])):
            if i < 3:
                layer = nn.Sequential(
                    nn.Conv2d(input_size, channels, kernel_size=1, bias=False),
                    nn.BatchNorm2d(channels),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(channels, output_size, kernel_size=3, padding=1, stride=2, bias=False),
                    nn.BatchNorm2d(output_size),
                    nn.ReLU(inplace=True),
                )
            else:
                layer = nn.Sequential(
                    nn.Conv2d(input_size, channels, kernel_size=1, bias=False),
                    nn.BatchNorm2d(channels),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(channels, output_size, kernel_size=3, bias=False),
                    nn.BatchNorm2d(output_size),
                    nn.ReLU(inplace=True),
                )

            self.additional_blocks.append(layer)

        self.additional_blocks = nn.ModuleList(self.additional_blocks)


    def _init_weights(self):
        layers = [*self.additional_blocks]
        for layer in layers:
            for param in layer.parameters():
                if param.dim() > 1: nn.init.xavier_uniform_(param)

    # def forward(self, x: Tensor) -> Dict[str, Tensor]:
    #     # L2 regularization + Rescaling of 1st block's feature map
    #     x = self.features(x)
    #     rescaled = self.scale_weight.view(1, -1, 1, 1) * F.normalize(x)
    #     output = [rescaled]

    #     # Calculating Feature maps for the rest blocks
    #     for block in self.extra:
    #         x = block(x)
    #         output.append(x)

    #     return OrderedDict([(str(i), v) for i, v in enumerate(output)])

    
    def forward(self, x):
        x = self.feature_extractor(x)

        detection_feed = [x]
        for l in self.additional_blocks:
            x = l(x)
            detection_feed.append(x)

        return OrderedDict([(str(i), v) for i, v in enumerate(detection_feed)])

def res_extractor(backbone):

  return SSDFeatureExtractorRES(backbone)