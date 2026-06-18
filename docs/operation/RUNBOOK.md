# 运行手册

## 本地启动

后端：

```bash
cd apps/api
python main.py
```

前端：

```bash
cd apps/web
npm install
npm run dev
```

运行一次试运行：

```bash
python core/pipeline/runner.py --mode demo
```

> 说明：后端统一入口为 `apps/api/main.py`，流水线统一入口为
> `core/pipeline/runner.py`。没有其他入口。

## 生产运行输入

唯一路径（canonical）：`data/inputs/real/apps.json`

不存在其他兼容路径。导入接口 `POST /api/real-inputs/apps` 也只写这一个文件。

## 产物位置

每次运行产物都在：`data/outputs/{jobId}/`

根目录不再放运行产物。
