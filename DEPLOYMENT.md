# ParseCove：Cloudflare Pages 部署

仓库：<https://github.com/joshua880604-web/parsecove>

正式域名：<https://parsecove.com>

本项目是静态网站。Python 标准库生成页面，浏览器执行转换功能；不需要服务器、数据库、Wrangler 或 API 密钥。

## 1. 连接 GitHub 并首次部署

1. 登录自己的 Cloudflare 账户，进入 **Workers & Pages**。
2. 选择 **Create application → Pages → Import an existing Git repository**。如果默认展示 Workers 创建向导，切换到 Pages。
3. 授权 GitHub，选择 `joshua880604-web/parsecove`；可以只授权这个仓库。
4. 按下表填写构建设置，然后选择 **Save and Deploy**。

| 配置 | 填写内容 |
| --- | --- |
| Project name | 优先填写 `parsecove`；若不可用，使用可用名称 |
| Production branch | `main` |
| Framework preset | `None` |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Root directory | 保持默认，使用仓库根目录 |
| Environment variables | 当前版本无需添加 |

部署成功后，以 Cloudflare 实际显示的 `*.pages.dev` 地址为准。不要预先假设项目名称或临时网址。后续推送到 `main` 将触发新的生产部署。

## 2. 检查临时网址

确认部署状态为成功，并打开首页和以下页面：

- `/unix-timestamp-converter/`
- `/px-to-rem/`
- `/rem-to-px/`
- `/base64/`
- `/base64url-decode/`
- `/base64-to-image/`
- `/image-to-base64/`
- `/guides/`
- `/guides/rem-vs-em/`
- `/guides/save-base64-image/`
- `/guides/unix-timestamp-seconds-vs-milliseconds/`
- `/guides/fix-invalid-base64/`
- `/about/`
- `/privacy/`

检查转换、复制、图片预览与下载；确认样式正常。刷新工具页应保持正常，访问不存在的路径应显示自定义 404 页面。

## 3. 绑定根域名 parsecove.com

Cloudflare Pages 绑定根域名，要求该域名作为 DNS zone 添加到同一个 Cloudflare 账户，并使用 Cloudflare 分配的 nameserver。域名注册商可以继续保留阿里云。

1. 在 Cloudflare 添加 `parsecove.com`，选择适合当前需求的套餐。
2. 核对导入的现有 DNS 记录；若存在邮箱等服务，保留对应 MX、TXT 等记录。
3. 在阿里云域名控制台修改 DNS 服务器，填写 Cloudflare 为此域名实际分配的两条 nameserver。此步骤是修改域名的 DNS 服务器，不是在解析列表中添加两条 NS 记录。
4. 等待 Cloudflare 域名状态变为 Active。
5. 打开 Pages 项目 → **Custom domains → Set up a domain**，添加 `parsecove.com`，按向导建立记录。
6. 同名的旧 Sites A/CNAME 记录如有冲突，在本次切换中替换为 Pages 向导要求的记录。Cloudflare Pages 与之前 Sites 的解析目标不同，不要沿用旧 Sites 的 IP 地址。
7. 等待自定义域名及 HTTPS 证书状态正常，再验证正式网址。

若暂时保留阿里云 DNS，可以先部署到 Cloudflare 实际提供的 `*.pages.dev` 地址；也可以先在 Pages 添加 `www.parsecove.com`，再在阿里云添加指向实际 Pages 地址的 CNAME。此方案只绑定 `www` 子域名，尚未完成根域名上线；代码目前的 canonical 使用根域名。

可在正式域名工作后添加 `www.parsecove.com`，并将其永久重定向到 `https://parsecove.com`，保留原路径和查询参数。任何重定向规则都应使用实际已配置的域名。

## 4. 正式上线检查

- `https://parsecove.com` 及七个工具页面均可直接访问，HTTPS 正常。
- 页面 canonical、`/sitemap.xml` 和 `/robots.txt` 均指向 `https://parsecove.com`。
- 在 Google Search Console 验证域名并提交 `https://parsecove.com/sitemap.xml`。无需提交临时 Pages 网址。
- 以 Cloudflare 的部署记录、实际 HTTP 响应和浏览器访问结果判断上线是否成功；仓库推送成功本身不代表已部署到 Cloudflare。
- 广告开关默认关闭，当前部署不需要 AdSense ID 或广告脚本。

## 官方参考

- <https://developers.cloudflare.com/pages/framework-guides/deploy-anything/>
- <https://developers.cloudflare.com/pages/configuration/git-integration/>
- <https://developers.cloudflare.com/pages/configuration/custom-domains/>
