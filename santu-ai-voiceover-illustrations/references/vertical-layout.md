# 黑底竖屏布局

默认画布：`1080x1920`。

## 区域

- `Y=0-100`：顶部呼吸区。
- `Y=120-820`：插画主体区。
- `Y=900-1240`：字幕安全区，剪辑层会加黑色柔边阴影带，但图片里仍应尽量保持黑底干净。
- `Y=1240-1580`：圆形头像和左右声波安全区。
- `Y=1600-1920`：底部呼吸区。

## 原则

- 重要图形只放上方插画主体区。
- 重要图形离左右边框和顶部都要有空余，不要贴边；后期会为平台安全区做等比例轻缩。
- 中部字幕区必须干净，不能有小字或关键箭头。
- 下方头像声波区必须干净，不能有关键物件。
- 黑底可以铺满全图，但内容不要铺满全图。
- 图内文字越少越好，尽量让字幕承担解释。
- 实际生图尺寸以文件为准；剪辑层会记录真实尺寸，并按抖音/视频号安全区等比例轻缩居中。

## Prompt 固定句

```text
Place all important drawing content in the upper illustration zone, roughly between 6% and 43% of the image height. Leave comfortable margins from the left, right, and top edges for Douyin/WeChat Channels safe areas. Keep the middle subtitle area and lower avatar + audio waveform area clean black.
```
