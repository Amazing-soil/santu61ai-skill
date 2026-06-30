# gpt-image2 黑底简笔画提示词模板

每张图单独写一个 prompt。主体说明和少量中文标注可以用中文写，视觉约束建议保留英文。

```text
Generate one standalone vertical 9:16 illustration for a Chinese business/AI voiceover video.

Visual style:
Pure black or near-black background (#050505). Minimalist white and light-gray simple line art, like a clean blackboard doodle sketch. Professional, sharp, quiet, business-oriented. Use very sparse accent color: blue for AI/system signal, orange for process/action, red for risk/warning. No gradients, no paper texture, no realistic scene, no poster lighting, no cyberpunk HUD, no robot cliche, no PPT, no UI panels.

Recurring character:
Include the Santu AI bespectacled suited little business operator as the main actor: a compact white-line doodle character wearing thin glasses, a simplified suit jacket, shirt, and small tie or lapel accent. The character must perform the key action that explains the idea, not stand as decoration. Do not make it a real portrait, cute mascot, Q-version cartoon, superhero, or luxury CEO poster figure.

Topic:
[这张图的主题]

Core idea:
[一句话说明这张图表达什么]

Composition:
[具体画面：戴眼镜西装小人在做什么，用什么物理隐喻、流程、对照或状态来表达。尽量用物件和动作，不要靠文字解释。]

Vertical layout:
Place all important drawing content in the upper illustration zone, roughly between 6% and 43% of the image height. Leave comfortable platform safe margins on all sides: no important object should touch the left, right, or top edge. Keep the middle subtitle area and lower avatar + audio waveform area clean black. The editing layer may add a black subtitle shadow band, but do not rely on it for important objects. Do not put important faces, arrows, icons, or labels in the middle-lower and bottom areas.

Suggested elements:
[元素 1] / [元素 2] / [元素 3]

Optional tiny Chinese labels:
[0-4 个短标签，每个 2-6 个汉字；不要长句]

Constraints:
One image explains only one idea. Keep the drawing sparse and readable on a phone. Avoid long text. Do not write a title. Do not add subtitles. Do not use white background. Do not fill the whole screen. No dense charts, no interface mockups, no cute cartoon mascot, no stock business illustration.
```

## 生成与保存

直接出图时，每张 prompt 对应一个确定文件名，例如：

```text
img-01-hook.png
img-02-tool-trap.png
img-03-simple-tool.png
```

图片生成后先从 `$CODEX_HOME/generated_images/...` 找到新增 PNG，再复制到项目 `public/media/images/`，确认文件可读。不要只把生图结果留在聊天窗口或默认生成目录里。
记录文件真实像素尺寸；如果生成结果是 `941x1672`，就按 `941x1672` 写入素材清单，剪辑层按平台安全区等比例轻缩并居中展示。

## 常用改写

如果图太白：

```text
Regenerate with a pure black background and white simple line art. Do not use a white canvas, paper texture, or light background.
```

如果图太满：

```text
Make the drawing cluster slightly smaller, keep comfortable margins from the left/right/top edges, and move all important elements into the upper illustration zone. Leave the middle subtitle area and lower avatar/waveform area clean black.
Keep the generated image as a full black-background asset; the editing timeline will record the real image size, apply proportional safe-zone scaling, and add a subtitle shadow safety band.
```

如果文字太多：

```text
Remove long text and keep only 0-4 tiny Chinese labels. The video subtitle will explain the idea, so the image should rely on objects and actions.
```
