# 若愚 · 全息闪卡工坊

**ruoyu-holo-card-studio · 个人增强版 v1.0.0**

> 本项目基于 [EverettFish](https://github.com/EverettFish) 的 [holo-card-studio](https://github.com/EverettFish/holo-card-studio) 升级和优化，并非从零原创，也不是上游官方版本。感谢原作者与贡献者的基础工作。原项目版权声明及 MIT 许可完整保留在 [LICENSE](LICENSE)。

原版建立了全息卡片的制作基础。我主要在此基础上完善个人视觉预设、配置兼容、批量构建、断点续跑、素材校验与交付保护，让重复制作更稳定、可检查。

## 能做什么

将描述或参考图制作成带独立图层、视差、镭射与闪星效果的卡片，输出 Blender 工程、GLB 模型、渲染图和 Three.js 交互网页。

新增与优化：

- `ruoyu-classic`：黑底细框、克制流光的默认参数，支持全身与半身构图。
- 同时支持标量和二维安全区缩放。
- 按输入与输出哈希缓存 Blender 构建和 GLB 导出，支持断点续跑。
- 批量入口记录每个项目的成功或失败。
- 保护用户修改过的场景和网页；显式替换前备份。
- 检查透明度、画布尺寸、空图和线稿背景，并提示边缘风险。
- Blender 设备检测、中文字体选择和网页背面文字方向修正。

## 作为 Skill 使用

将本仓库克隆到项目的 Skill 目录：

```sh
git clone https://github.com/yzhe3778-ai/ruoyu-holo-card-studio.git .agents/skills/ruoyu-holo-card-studio
```

重新加载支持项目 Skill 的 agent 后，可以说：

> 使用 $ruoyu-holo-card-studio，把这批图片制作成全息闪卡，输出到我指定的目录。

完整规则见 [SKILL.md](SKILL.md)。需要 Python 3.10+、Pillow、Blender 和 Node.js/npm。图像生成需要 agent 环境提供对应工具；项目不包含账号、密钥或生图服务。使用本地 Blender CLI 即可，无须 Blender MCP。

## 从已准备的图层构建

以下命令在仓库根目录执行：

```sh
python3 -m pip install Pillow
python3 scripts/prepare_config.py --project /path/to/card --title "卡片名称" --layout full
```

准备同尺寸的 `assets/subject.png`（透明主体）、`background.png`（完整背景）、`lineart.png`（黑线白底线稿）。文字图层缺失时由流水线生成；中文字体缺失时需在配置中指定字体文件。

```sh
python3 scripts/run_pipeline.py --project /path/to/card --resume --blender /path/to/blender
```

构建后进入输出目录的 `web` 文件夹运行 `npm start`，按终端提示打开本地预览。批量清单、续跑和替换规则见 [批量工作流](references/batch.md)。

## 能力边界

- CLI 从已准备素材开始，不是一条命令直接完成所有 AI 拆图。
- ImageGen 参考重绘不等于保留原像素的无损抠图；不能保证保真时先征求用户同意。
- 批量脚本负责逐卡构建，目前不自动生成图集总览页面。
- 技术校验不能替代拆层、裁切和视觉质量验收。
- PNG 不保留动态交互；网页重建 Blender 材质，不保证逐像素一致。

## 验证与许可

```sh
python3 scripts/test_workflow.py
node --check assets/web-template/app.js
```

v1.0.0 已通过 13 项回归测试，并在本地完成实际 Blender 渲染、GLB 导出、缓存续跑、批量失败记录及网页正反面检查。详见 [来源与验证记录](references/provenance.md)。

代码采用 [MIT License](LICENSE)。不分发用户图片、角色素材、生成工程、缓存或依赖目录；素材版权不因软件许可而转移。上游基线：[`7d09e040`](https://github.com/EverettFish/holo-card-studio/commit/7d09e040427319d291164f0c1ac78f8ca0638f18)。
