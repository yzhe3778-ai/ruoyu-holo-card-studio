---
name: ruoyu-holo-card-studio
description: 若愚的全息闪卡工坊。将描述或参考图制作成独立拆层、视差、镭射、闪星的 Blender 与 Three.js 卡牌，支持单卡和可续跑的批量制作。适用于全息卡片与卡片图集，不用于普通海报。
---

# 若愚 · 全息闪卡工坊

个人增强版，基于 EverettFish/holo-card-studio，保留 MIT 许可与署名，见 [来源说明](references/provenance.md)。默认使用黑底细框、克制流光的 ruoyu-classic 预设；不把示例角色、主题色或招式套到其他题材。

## 素材模式

- 用户给原图：默认保真意图。先说明可用工具能否保留原像素；不能保证时，先问是否接受参考重绘，不得将 ImageGen 重绘称作无损抠图。
- 用户接受重绘或从描述创作：使用内置 ImageGen，不擅自改用收费 API 或陌生服务。
- 有认可样片：锁定其配置与资产哈希，其他卡片单独调取景，不覆盖认可样片。

## 制作流程

1. 读取 [拆层说明](references/art-direction.md)，检查图片，输出放在用户指定项目，不放进 Skill。
2. `scripts/prepare_config.py --project <目录> --title <名称> --layout full` 创建配置。半身裁切图用 portrait。已有配置不会覆盖；名称、招式、颜色、安全区均可配置，无角色编号硬编码。
3. 生成 assets/subject.png（真透明人物）、background.png（补全背景）、lineart.png（配准黑线白底）；文字用 generate_typography.py。同画布，默认 1024×1536。每层最多初次加两次重试，失败停下说明，不重做已通过层。
4. `validate_assets.py <项目>` 拒绝无 alpha、透明不足、全空人物、非白底线稿和尺寸不一致。触边和线稿越界提示需人工复查，不是自动证明配准。失败不得发布。
5. `run_pipeline.py --project <项目> --resume` 按输入和输出哈希跳过已验证阶段。批量及覆盖规则见 [批量工作流](references/batch.md)。CLI 从已准备素材开始，图像生成仍由 agent 调用内置工具，不宣称 CLI 全自动生图。
6. 按 [验收要求](references/verification.md) 实际浏览器检查。每张至少查正面、左右倾斜、姓名和裁切；代表卡测试正负深度、镭射对照、翻面、保存、390px。技术通过不等于视觉认可。
7. 交付 URL、工程、实际渲染及验收范围。PNG 不含动态视差；网页 GLSL 重建 Blender 材质，不保证逐像素一致。仅在明确请求时公开发布。

## 不变量

- Blender 三平面保留物体 X=90°，导出真实网格，以 web_front/web_edge/web_back/web_gold 为契约。
- 网页用卡牌根节点逆旋转计算视线，不用 glTF 转换后的面网格坐标；V 只还原一次。测试两种转向和深度符号。
- 安全区与可调视差分离；缩放可为标量或二维数组，两端必须兼容。
- 不用过曝掩盖抠图或线稿错位。镭射随视角变化，星点稀疏，文字最后合成。
- .holo-state.json 只记录技术阶段，不记录未经确认的审美通过。用户改过的网页和场景必须保护，显式替换先备份。
- Skill 仅分发代码文字。打包用 package_skill.py，不带用户图片、Blender 文件、缓存、依赖或密钥。
