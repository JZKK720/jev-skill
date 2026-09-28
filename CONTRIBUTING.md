# Contributing

Thanks for helping grow Awesome Jev! English and Chinese are both welcome.

- **Have something to add?** Open an [issue](https://github.com/wuyoscar/jev-skill/issues/new/choose) first, especially for a new project, use case or larger change. Include a link and a short explanation of why it belongs here. Check existing entries and issues to avoid duplicates.
- **Prefer to send a PR?** That's welcome too. Keep it focused, explain the change and check it before asking for review. For catalog additions, verify the source links, keep descriptions factual, disclose if you maintain the project, and update both READMEs and the project count where needed. Distinguish author demos from your own test results.
- **No third-party API relays.** Jev calls go only to OpenRouter or the official TypeSafe API. PRs that add another endpoint, base URL, provider option or API key for a relay, reseller or proxy will be closed, even if it speaks the same protocol or is free: we cannot verify how it handles users' data and keys, and a built-in route works as promotion. The same applies to catalog entries that are themselves relays or key shops. `tests/test_provider_policy.py` enforces this.
- **Show what you checked.** Include test commands and results, or explain what was not tested. Run `python3 -m unittest discover -s tests -v` for code or catalog-count changes, and `git diff --check` for every PR. Don't include API keys or private data. Paid API calls are not required to contribute.

Maintainers review PRs before merging. Please address review feedback; opening a PR does not guarantee inclusion.

## 中文

欢迎一起完善 Awesome Jev，中英文都可以。

- **想加东西？** 建议先提 [issue](https://github.com/wuyoscar/jev-skill/issues/new/choose)，特别是新项目、新用法或较大的改动。附上链接，简单说说为什么值得收录，先看看有没有重复条目或 issue。
- **直接提 PR 也欢迎。** 一次围绕一件事，说明改了什么，提交前自己检查。收录项目时确认链接有效、描述属实；如果是自己的项目，请说明。需要时同步中英文 README 和项目数量，区分作者演示和自己的实测。
- **不接受第三方 API 中转站。** Jev 调用只走 OpenRouter 或 TypeSafe 官方 API。新增中转站、转售或代理服务的端点、base URL、provider 选项或 API key 的 PR 会被关闭，协议相同或限时免费也一样：这类服务如何处理用户数据和 key 无法核实，内置入口也等于替它引流。本身是中转站或卖 key 站点的目录条目同样不收。`tests/test_provider_policy.py` 会自动检查。
- **写清楚检查结果。** 附测试命令和结果，没测的也直说。代码或目录数量变更运行 `python3 -m unittest discover -s tests -v`，所有 PR 运行 `git diff --check`。不要提交 API key 或私人数据，也不要求为了贡献进行付费调用。

PR 由维护者审核后合并，请处理 review 意见；提交不代表一定收录。
