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

后端 entrypoint 流程：等待数据库就绪 → `create_all` 建表 → `migrate` 幂等补列/约束 → seed 初始数据 → 启动 uvicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 Password），`/api/auth/login`、`/api/auth/me`
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`
3. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
4. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**
5. **FeedEvent 投喂（含冲销凭证）**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`
   - 投喂记录**不允许物理删除**；错误投喂通过「冲销凭证」负向抵消（`POST /api/feed-events/{id}/reverse`）
   - 冲销字段：原投喂编号 `reversalOfId`、冲销千克（由服务端取负值，**必须且必然等于原投喂千克**）、原因（**至少 6 字**）、冲销时刻、操作人（取当前登录用户，无需前端传入）
   - **同一原投喂只许冲销一次**（唯一约束 + 接口双重校验）；冲销凭证本身不可再冲销
   - 冲销后原投喂仍保留在列表中并带「已冲销」标记，冲销凭证为负千克行同时列出
   - 列表默认返回全部行；`?validOnly=true` 仅返回有效投喂（排除冲销凭证行与已冲销的原投喂）
6. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日**有效**投喂总量 kg（冲销凭证与已冲销原投喂均不计入，与投喂页「仅有效投喂」合计口径完全一致，即已冲销千克被全额扣除）

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
python -c "from app.migrate import migrate; migrate()"
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
