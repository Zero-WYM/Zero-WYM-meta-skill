# 发布链路 · gh 开源发布

> 前置：`gh` CLI 已装且 `gh auth login` 已登录（本机已验证 account `Zero-WYM`，scopes: repo/workflow/admin:org）。未登录时脚本**自动降级**为"本地打包 + 步骤清单"，不报错、不假跑。

## 链路顺序

```
secret_scan（必须零命中）
   → 生成/更新 README（不含个人凭据、不含原包品牌码）
   → 特性分支 feature/publish-<name>
   → commit（仅本包文件）
   → 推分支 → 开 PR 到默认分支
   → 等合并（或手动合并）
   → 打 tag vX.Y.Z + GitHub Release
   → 安装验证（gh api 或 git clone 验证可拉取）
```

## 硬规则

1. **禁止直推主分支**（main/master）。所有发布内容走 PR，留 review 痕迹。
2. **密钥扫描不过 = 阻断发布**。任何 api_key / token / ghp_ / 私钥命中，立即停止并报告。
3. **不写个人凭据进包**：README 不嵌你的 token、不嵌原包作者的头像/打赏/公号二维码。
4. **Release 与 tag 绑定**，版本号语义化（vMAJOR.MINOR.PATCH）。
5. 发布是**对外不可逆写操作**，脚本默认 `--dry-run`；真正 push/PR/Release 需用户显式去掉 dry-run 并确认。

## 脚本调用

```bash
# 预检（干跑，不落远端）
"$PY" scripts/publish_skill.py --skill-dir . --repo <Owner>/<Repo> --dry-run

# 真实发布（去掉 --dry-run 前，用户需显式确认）
"$PY" scripts/publish_skill.py --skill-dir . --repo <Owner>/<Repo> --version v0.1.0
```

## 未登录降级行为

`publish_skill.py` 若检测到 `gh` 缺失或未登录：
- 打印清晰指引（`winget install --id GitHub.cli` / `gh auth login --web`）。
- 仍执行**本地可验部分**：密钥扫描、ZIP 打包、生成 `PUBLISH_STEPS.md` 手工步骤清单。
- 在退出码与 stdout 明确标注"发布未实测 / 需你本地登录后运行"，不假报完成。

## 回收与回滚

- 若 PR 未合并即发现问题：`gh pr close` + 删分支。
- 若 Release 已发需撤回：`gh release delete` + `git push --delete origin <tag>`（谨慎，属公开操作）。
- 这些回收动作**同样需用户显式确认**，脚本不自动执行。
