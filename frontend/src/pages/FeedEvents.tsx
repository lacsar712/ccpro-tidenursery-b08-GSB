import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DashboardStats, FeedEvent, Pond } from '../types'

function nowLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const empty = {
  pondId: 0,
  fedAt: nowLocal(),
  feedType: '轮虫',
  amountKg: 1,
  operatorName: '水质技术员',
}

export default function FeedEvents() {
  const [ponds, setPonds] = useState<Pond[]>([])
  const [rows, setRows] = useState<FeedEvent[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [form, setForm] = useState(empty)
  const [validOnly, setValidOnly] = useState(false)
  const [reversing, setReversing] = useState<FeedEvent | null>(null)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const query = validOnly ? '?validOnly=true' : ''
    const [ps, es, st] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<FeedEvent[]>(`/api/feed-events${query}`),
      api<DashboardStats>('/api/dashboard/stats'),
    ])
    setPonds(ps)
    setRows(es)
    setStats(st)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [validOnly])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/feed-events', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          fedAt: new Date(form.fedAt).toISOString(),
        }),
      })
      setForm((f) => ({ ...empty, pondId: f.pondId, fedAt: nowLocal() }))
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  function startReverse(row: FeedEvent) {
    setError('')
    setReason('')
    setReversing(row)
  }

  async function onReverseSubmit(e: FormEvent) {
    e.preventDefault()
    if (!reversing) return
    setError('')
    if (reason.trim().length < 6) {
      setError('冲销原因至少 6 字')
      return
    }
    try {
      await api(`/api/feed-events/${reversing.id}/reversal`, {
        method: 'POST',
        body: JSON.stringify({
          amountKg: reversing.amountKg,
          reason: reason.trim(),
        }),
      })
      setReversing(null)
      setReason('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '冲销失败')
    }
  }

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} (${p.species})` : `#${id}`
  }

  return (
    <div>
      <header className="page-header">
        <h1>投喂事件</h1>
        <p className="muted">记录饵料类型、投喂量与操作人；错误投喂以冲销凭证负向抵消，不做物理删除</p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          塘口
          <select
            value={form.pondId}
            onChange={(e) => setForm({ ...form, pondId: Number(e.target.value) })}
            required
          >
            {ponds.map((p) => (
              <option key={p.id} value={p.id}>
                {p.pondCode} · {p.species}
              </option>
            ))}
          </select>
        </label>
        <label>
          投喂时间
          <input
            type="datetime-local"
            value={form.fedAt}
            onChange={(e) => setForm({ ...form, fedAt: e.target.value })}
            required
          />
        </label>
        <label>
          饵料类型
          <input
            value={form.feedType}
            onChange={(e) => setForm({ ...form, feedType: e.target.value })}
            required
          />
        </label>
        <label>
          投喂量 kg
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.amountKg}
            onChange={(e) => setForm({ ...form, amountKg: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          操作人
          <input
            value={form.operatorName}
            onChange={(e) => setForm({ ...form, operatorName: e.target.value })}
            required
          />
        </label>
        <button type="submit" className="btn primary">
          登记投喂
        </button>
      </form>

      {reversing && (
        <form className="panel form-grid" onSubmit={onReverseSubmit}>
          <h3 className="panel-title span-2">冲销凭证 · 原投喂 #{reversing.id}</h3>
          <p className="hint span-2">
            {pondLabel(reversing.pondId)} · {new Date(reversing.fedAt).toLocaleString()} ·{' '}
            {reversing.feedType} · {reversing.amountKg} kg · 原操作人 {reversing.operatorName}
          </p>
          <label>
            冲销 kg（必须等于原投喂千克）
            <input type="number" value={reversing.amountKg} readOnly />
          </label>
          <label>
            冲销原因（至少 6 字）
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              minLength={6}
              required
            />
          </label>
          <p className="hint span-2">
            冲销时刻以提交时的服务器时间入账，操作人记为当前登录用户；冲销后原记录保留并标记「已冲销」。
          </p>
          <div className="span-2 btn-row">
            <button type="submit" className="btn primary">
              提交冲销
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setReversing(null)
                setReason('')
              }}
            >
              取消
            </button>
          </div>
        </form>
      )}

      <div className="panel toolbar">
        <label className="check">
          <input
            type="checkbox"
            checked={validOnly}
            onChange={(e) => setValidOnly(e.target.checked)}
          />
          仅看有效投喂（排除已冲销）
        </label>
        <span className="hint">
          近 7 日有效投喂合计：
          <strong>{stats ? stats.feedKgLast7d.toFixed(2) : '—'} kg</strong>
          （已扣除冲销，与仪表盘口径一致）
        </span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>塘口</th>
              <th>投喂时间</th>
              <th>饵料</th>
              <th>数量 kg</th>
              <th>操作人</th>
              <th>状态</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.reversal ? 'row-voided' : ''}>
                <td>{r.id}</td>
                <td>{pondLabel(r.pondId)}</td>
                <td>{new Date(r.fedAt).toLocaleString()}</td>
                <td>{r.feedType}</td>
                <td>{r.amountKg}</td>
                <td>{r.operatorName}</td>
                <td>
                  {r.reversal ? (
                    <div className="void-info">
                      <span className="badge voided">已冲销</span>
                      <span className="hint">
                        冲销 {r.reversal.amountKg} kg ·{' '}
                        {new Date(r.reversal.reversedAt).toLocaleString()} ·{' '}
                        {r.reversal.operatorName}
                        <br />
                        原因：{r.reversal.reason}
                      </span>
                    </div>
                  ) : (
                    <span className="badge stocked">有效</span>
                  )}
                </td>
                <td>
                  {r.reversal ? (
                    '—'
                  ) : (
                    <button className="btn ghost" onClick={() => startReverse(r)}>
                      冲销
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
