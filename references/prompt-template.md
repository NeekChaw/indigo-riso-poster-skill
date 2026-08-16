# 生成提示词模板 / Prompt Template

生成前先确定：色卡（见 color-cards.md）、构图类型、主体意象。把下面模板里的占位符替换掉，再拼接 halftone-spec.md 里的网点措辞段落。

## 中文模板

```text
生成一张限定"靛蓝 + 米白"双色系的极简海报，采用丝网印刷（riso print）双色套印质感，<横向 16:9 / 竖版 3:5> 构图。

色卡：
纸基色（Ground）：<色值>，作为留白底色
主墨色（Ink）：<色值>，作为唯一的大面积实色
雾层色（Mist）：<色值>，仅用于表现远近层次，不大面积铺开

主体意象：
<用户提炼出的唯一视觉锚点描述，例如"一座层叠的雪山，近处山体为实色靛蓝，远处山脉逐渐被雾层色和网点稀释">

构图类型：<横向地平线型 / 静态陈列型 / 扩散消散型 / 密度延伸型 / 纵向延伸型（竖版专用）>
<代入 halftone-spec.md 中对应构图类型的面积上限和位置规则>

网点渐变：
使用半调网点（halftone dot）表现渐变与材质，网点从实色逐渐过渡到稀疏散点直至消失，方向要符合物理逻辑（扩散/阴影/空气透视），禁止使用传统模糊渐变。网点为圆形，尺寸细密，接近丝网印刷质感。整体叠加一层极轻的做旧纸张颗粒感。

[可选，仅在需要表达光/生命感时加入，全图最多一处]
专色点缀（Accent）：<描述唯一的光源点，如"一扇窗透出的光"、"一盏远处的灯">，色值 <暖金色，如 #D9A85C>，面积不超过画面 5%，是全图唯一跳出蓝白色系的元素。

[默认必须包含，除非用户明确说不要文字；文字与画面一次生成，不做后期叠加]
文字：<按 typography-spec.md 写完整印刷事件描述——确切文字内容（从意象提炼一句极简的话，中文一句话或英文≤5词）+ 四变量（墨色浓度档位 / 笔画性格 / 空间关系：沉底·同层·浮面 / 时间感）+ 与画面物理逻辑的关系（消散方向、位置依据）+ 至多一处"破"（断墨/压痕/被磨损吃掉）。文字颜色只能使用上述色卡角色色值。示例见 typography-spec.md。>

禁止出现：
靛蓝和米白之外的任何色相（除非上方明确指定了专色点缀）；玻璃质感/3D渲染反光；赛博朋克霓虹；传统径向或线性模糊渐变；多个并列的视觉主体；圆滑卡通描边；无意义的大段文字。

画面必须包含上方"文字"段指定的极简文字，除非用户明确要求不带字。
```

## English Template

```text
Generate a minimal poster limited to an indigo-blue and cream duotone palette, in the visual language of duotone riso print reproduction. <Horizontal 16:9 / Portrait 3:5> composition.

Color roles:
Ground (paper base): <hex>, the dominant blank/negative space color
Ink (primary solid): <hex>, the only large solid-fill color
Mist (mid-tone): <hex>, used only for atmospheric depth on secondary/distant shapes, never as a large fill

Subject:
<single visual anchor description, e.g. "a layered mountain range, the nearest peak solid Ink blue, distant ranges dissolving into Mist tone and halftone dots">

Composition type: <horizon-split / single-point-negative-space / organic-diffusion / vertical-extension (portrait only)>
<insert the relevant area-limit / placement rule from halftone-spec.md>

Halftone treatment:
Use halftone dot gradients — NOT smooth gradient blur — for every tonal transition and texture. Dots go from solid, to dense, to sparse, to none, with direction tied to the physical logic of the shape (diffusion, shadow, atmospheric perspective). Dots are circular, fine, and dense, evoking screen-print / riso reproduction. Add a very light aged-paper grain overlay across the whole image.

Avoid:
any hue outside the indigo-and-cream family; glass/3D render reflections; cyberpunk neon; traditional radial or linear gradient blur; multiple competing focal subjects; smooth cartoon outlines; unnecessary large blocks of text.

[Required by default — only omit if user explicitly requests no text; text and image are generated in one pass, no post-processing overlay]
Text: <full print-event description per typography-spec.md: exact wording (one minimal sentence derived from the imagery, one Chinese sentence or ≤5 English words) + the four variables (ink weight / stroke character / spatial layer: sunken·same-layer·overprinted / age) + how the text obeys the image's physical logic (diffusion direction, placement rationale) + at most one "break" (starved ink, impression-only missing word, worn edge). Text color must reuse one of the color roles above. See typography-spec.md for examples.>

The image must include the minimal text specified in the Text section above, unless the user explicitly requested no text. Text must be spelled exactly as specified — misspelled or garbled text is a failed generation.
```

## 使用提示

- 主体意象的描述越具体（近景/远景怎么分、哪部分该用哪个色阶），生成结果越稳定；不要只写"一座山"，要写清楚"近处实色、远处雾化"这种层次分配
- 每次生成后把实际用的完整 prompt 记录下来作为输出三件套的一部分，方便用户在此基础上微调重跑
- 如果连续两次都出现"翻车模式"（见 halftone-spec.md），优先怀疑是否遗漏了否定式约束（"NOT gradient blur"这类），而不是继续加正面描述词
