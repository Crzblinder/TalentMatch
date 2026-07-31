# TalentMatch Edge 扩展

本目录包含 Microsoft Edge 浏览器扩展所需的全部文件。

## 目录结构

```
extension/
├── manifest.json      # 扩展清单（Manifest V3）
├── sidepanel.html     # 侧边栏入口页面
├── sidepanel.js       # 侧边栏逻辑：探测后端、加载前端
├── popup.html         # 工具栏图标点击弹窗
├── popup.js           # 弹窗逻辑
├── background.js      # Service Worker
├── options.html       # 扩展选项页
├── options.js         # 选项页逻辑
├── icons/             # 扩展图标
├── dist/              # 前端构建产物（运行时生成，不提交）
└── build.js           # 打包脚本
```

## 前置条件

- 已安装 Node.js 18+ 与 Python 3.11+
- TalentMatch 后端服务可在本地运行（默认 `http://127.0.0.1:8000`）

## 打包扩展

在项目根目录执行：

```powershell
node extension/build.js
```

脚本会：
1. 以扩展模式构建前端（资源使用相对路径）。
2. 将 `frontend/dist` 复制到 `extension/dist`。

## 手动加载（侧载）到 Edge

1. 启动 TalentMatch 后端：
   ```powershell
   python scripts/start.py --backend-only
   ```
2. 打开 Microsoft Edge，访问 `edge://extensions/`。
3. 打开右上角“开发人员模式”开关。
4. 点击“加载解压缩的扩展”。
5. 选择项目根目录下的 `extension` 文件夹。
6. 扩展出现在列表中，点击工具栏图标即可在侧边栏使用 TalentMatch。

## 修改后端地址

若后端不在默认地址，右键点击扩展图标 → “扩展选项”，修改“后端服务地址”后保存。

## 注意事项

- `extension/dist/` 是构建产物，已加入 `.gitignore`，请勿提交。
- 扩展依赖本地运行的后端，因此必须先启动后端才能正常使用。
