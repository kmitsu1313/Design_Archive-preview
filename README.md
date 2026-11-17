# Design Archive · 分支预览大厅

[打开预览大厅](https://kmitsu1313.github.io/Design_Archive-preview/) · [原项目仓库](https://github.com/kmitsu1313/-Design_Archive) · [正式网站](https://kmitsu1313.github.io/-Design_Archive/)

这里用于检查不同分支的完整网页效果。选择分支即可预览，也可以独立打开并分享链接。每个人的选择互不影响，不会修改或合并原项目代码。

## 如何更新

同学仍在原项目仓库开发：创建分支、修改、推送、提交 PR。此仓库通过 GitHub Actions 约每 30 分钟检查原仓库的全部远程分支，发现变化后重新发布。定时任务可能延迟；上课前可在 **Actions → Refresh branch previews → Run workflow** 手动刷新。仅本地修改、尚未推送的代码不会出现。外部 fork 的分支暂不收录。

`main` 和《问道》的 `feature/wendao-layout` 是最初的两个测试版本。PR 对应目录使用 `pr-编号/`，其余分支使用稳定的分支名哈希；将页面地址发给同学即可分享所选版本。新建 PR 后目录会变化，请使用大厅里的新链接。

## 实现原理

自动化读取公开的分支和 PR 信息，按精确提交 SHA 下载文件，分别复制到独立目录，再生成版本清单与大厅。大厅用下拉框切换 iframe，并提供独立打开入口。页面和资源保持项目相对路径；根路径或写死的正式网址需要在原项目修正。

构建只复制静态文件，不执行原项目脚本或工作流。只发布网页资源，排除隐藏目录、Markdown、PDF 和 CNAME。发布使用本仓库的 GitHub Pages 权限，不需要原仓库写入权限，也不需要额外保存个人 token。

多个更新任务排队执行，每次一起发布所有版本。分支删除后，其预览在下次发布时清理；关闭 PR 不会删除仍存在的分支预览。源代码不变时，定时任务跳过重复发布。构建失败时保留上一版网站。

完整副本会重复占用图片和字体空间。构建在总文件超过 900 MB 时停止，以避免超过 Pages 的 1 GB 限制；可删除不再需要的源分支，或后续增加资源去重。GitHub 可能暂停长期没有仓库活动的定时工作流，可在 Actions 中重新启用。

## 文件

- `web/`：大厅页面、样式和交互。
- `scripts/build.py`：获取分支并生成 `_site/`，仅使用 Python 标准库及 Git。
- `.github/workflows/preview.yml`：定时检查、手动刷新和 Pages 发布。
- `_site/`：临时构建结果，通过 Actions artifact 发布，不提交到仓库。

正式网站继续由原仓库的 `main` 发布；合并 PR 仍在原仓库进行。
