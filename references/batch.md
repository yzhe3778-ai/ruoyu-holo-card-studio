# 批量与续跑

在用户输出目录建立 batch.json，例如 `{"projects":["cards/01","cards/02"]}`。每个目录需有 card-config.json 与四层素材（缺少文字时脚本生成）。路径限定清单目录之内。

`python scripts/batch.py <batch.json> --dry-run` 只列命令，不生图、不写状态。

`python scripts/batch.py <batch.json> --blender <可执行文件>` 逐项构建，默认续跑；个别失败继续其他卡，最终非零退出，batch-status.json 如实记录结果。没有无限自动重试。

单卡可用 `run_pipeline.py --project <目录> --resume`。修改素材、配置、构建脚本或输出会使对应缓存失效。失败阶段保留现场；若阶段产生了未登记的部分输出，先检查它们，再显式用 --replace-output 备份重跑，不静默覆盖。

模板受 .holo-template.json 管理。用户修改过的同名页面会阻止同步；明确要升级时 --replace-web 先备份到 web/.holo-backups/。未被管理的 Blender/GLB 输出同样需 --replace-output。这些选项不是批量默认值。

自带文字 PNG 视为用户素材；修改名称后需同步修改该文字层。流水线自己生成的文字带哈希，配置更新时可安全重建；用户手改过的文字不会无提示覆盖。

素材模式、提示词、重试和选图由 agent 编排，CLI 不调用付费生图服务。不把 CLI 的 built_needs_review 说成用户已认可。

图集交付：先完成独立卡牌并逐卡验收，再按用户要求建立缩略图目录或图集页面，不将未拆层原图冒充完成卡面。本版批量入口不自动生成总图集页面。
