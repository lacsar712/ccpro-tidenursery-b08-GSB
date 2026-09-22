# TideNursery-01 · 潮汐育苗台账

海水育苗场「塘口水质采样与投喂事件」台账种子项目（非库存 / 电商 / 医院）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose · passlib(bcrypt) · uvicorn |
| 前端 | React 18 · Vite · TypeScript · React Router v6 |
| 数据库 | PostgreSQL 15 |
| 部署 | docker-compose · 前端 Nginx 反代 `/api` |

## 端口与账号

| 服务 | 端口 |
| --- | --- |
| 前端 | **3400** |
| 后端 API | **8400** |
| PostgreSQL | **5434** |

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 场长 |
| `technician` | `123456` | 水质技术员 |

## 一键启动

```bash
cd TideNursery-01
docker compose up --build
```

启动后访问：

- 前端：http://localhost:3400
- 后端健康检查：http://localhost:8400/api/health
- API 文档：http://localhost:8400/docs

后端 entrypoint 流程：等待数据库就绪 → `create_all` 建表 → seed 初始数据 → 启动 uvicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 Password），`/api/auth/login`、`/api/auth/me`
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`
3. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
4. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**
5. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`；**不允许物理删除**，错误投喂以冲销凭证负向抵消
6. **FeedReversal 冲销凭证**：`feedEventId`、`amountKg`、`reason`、`reversedAt`、`operatorName`
7. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日有效投喂 kg（已扣除冲销）

## 冲销与统计

- 投喂事件只增不删：登记错误时，在投喂页点击「冲销」或 `POST /api/feed-events/{id}/reversal` 开具冲销凭证，负向抵消原投喂。
- 冲销字段：原投喂编号 `feedEventId`、冲销千克 `amountKg`、原因 `reason`、冲销时刻 `reversedAt`（服务器入账时间）、操作人 `operatorName`（当前登录用户）。
- 校验规则：`amountKg` **必须等于原投喂千克**；`reason` **至少 6 字**；同一原投喂**仅可冲销一次**（`feed_event_id` 唯一约束），违反返回 **400**。
- 列表口径：默认列表保留全部原始行，已冲销行带「已冲销」标记及凭证信息；`GET /api/feed-events?validOnly=true` 仅返回有效投喂（排除已冲销）。
- 统计口径：仪表盘「近 7 日有效投喂 kg」与投喂页「近 7 日有效投喂合计」同源同口径，均**扣除已冲销**。
- 种子数据内含一笔可冲销投喂（A-02 塘 · 卤虫无节幼体 · 0.6 kg），可直接体验冲销流程。

## 前端页面

Login · Dashboard · Hatcheries · Ponds · WaterSamples · FeedEvents

## 本地开发（可选）

```bash
# 数据库（或用 compose 只起 db）
docker compose up -d db

# 后端
cd backend
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://tidenursery:tidenursery@localhost:5434/tidenursery
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8400

# 前端
cd frontend
npm install
npm run dev
```

## 目录结构

```
TideNursery-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth.py
│       ├── seed.py
│       ├── models/
│       ├── schemas/
│       └── routers/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        ├── components/
        └── api/
```
