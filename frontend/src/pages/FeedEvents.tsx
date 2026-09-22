import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DashboardStats, FeedEvent, Pond, User } from '../types'

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
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [validOnly, setValidOnly] = useState(false)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [me, setMe] = useState<User | null>(null)
  const [reversing, setReversing] = useState<FeedEvent | null>(null)

  async function load() {
    const [ps, es, st, u] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<FeedEvent[]>(`/api/feed-events${validOnly ? '?validOnly=true' : ''}`),
      api<DashboardStats>('/api/dashboard/stats'),
      api<User>('/api/auth/me'),
    ])
    setPonds(ps)
    setRows(es)
    setStats(st)
    setMe(u)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} (${p.species})` : `#${id}`
  }

  return (
    <div>
      <header className="page-header">
        <h1>投喂事件</h1>
        <p className="muted">
          记录饵料类型、投喂量与操作人；错误投喂不可物理删除，须通过冲销凭证负向抵消
        </p>
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

      <div className="toolbar panel">
        <label className="check-label">
          <input
            type="checkbox"
            checked={validOnly}
            onChange={(e) => setValidOnly(e.target.checked)}
          />
          仅有效投喂（排除已冲销与冲销凭证）
        </label>
        <div className="effective-sum">
          近 7 日有效投喂合计：
          <strong>{stats ? stats.feedKgLast7d.toFixed(2) : '—'}</strong> kg
          <span className="hint">（与运行看板口径一致，已扣除已冲销）</span>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>编号</th>
              <th>塘口</th>
              <th>时间</th>
              <th>饵料</th>
              <th>数量 kg</th>
              <th>操作人</th>
              <th>状态 / 冲销信息</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isVoucher = r.reversalOfId != null
              return (
                <tr key={r.id} className={isVoucher ? 'row-voucher' : undefined}>
                  <td>{r.id}</td>
                  <td>{pondLabel(r.pondId)}</td>
                  <td>{new Date(r.fedAt).toLocaleString()}</td>
                  <td>{r.feedType}</td>
                  <td className={isVoucher ? 'amount-neg' : undefined}>{r.amountKg}</td>
                  <td>{r.operatorName}</td>
                  <td>
                    {isVoucher ? (
                      <div>
                        <span className="badge voucher">冲销凭证 · 原投喂 #{r.reversalOfId}</span>
                        <div className="cell-sub">
                          {r.reversedAt && `冲销时刻 ${new Date(r.reversedAt).toLocaleString()}`}
                          {r.reversedBy && ` · 操作人 ${r.reversedBy}`}
                          {r.reversalReason && <div>原因：{r.reversalReason}</div>}
                        </div>
                      </div>
                    ) : r.isReversed ? (
                      <span className="badge reversed">已冲销</span>
                    ) : (
                      <span className="badge">有效</span>
                    )}
                  </td>
                  <td>
                    {!isVoucher && !r.isReversed && (
                      <button className="btn ghost" onClick={() => setReversing(r)}>
                        冲销
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {reversing && (
        <ReverseDialog
          item={reversing}
          operatorName={me?.display_name ?? ''}
          onClose={() => setReversing(null)}
          onDone={async () => {
            setReversing(null)
            await load()
          }}
          onError={(msg) => setError(msg)}
        />
      )}
    </div>
  )
}

function ReverseDialog({
  item,
  operatorName,
  onClose,
  onDone,
  onError,
}: {
  item: FeedEvent
  operatorName: string
  onClose: () => void
  onDone: () => Promise<void>
  onError: (msg: string) => void
}) {
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (reason.trim().length < 6) {
      onError('冲销原因至少 6 个字')
      return
    }
    setSubmitting(true)
    try {
      await api(`/api/feed-events/${item.id}/reverse`, {
        method: 'POST',
        body: JSON.stringify({ reason: reason.trim() }),
      })
      await onDone()
    } catch (err) {
      onError(err instanceof Error ? err.message : '冲销失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <h2>发起冲销</h2>
        <p className="hint">
          冲销将生成一笔负向凭证，原投喂保留并标记为「已冲销」；同一投喂只能冲销一次。
        </p>
        <form className="form-stack" onSubmit={submit}>
          <label>
            原投喂编号
            <input value={`#${item.id}`} disabled />
          </label>
          <label>
            冲销千克（必须等于原投喂千克）
            <input value={`-${item.amountKg}`} disabled />
          </label>
          <label>
            冲销原因（至少 6 字）
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="例如：饵料品种登记错误，实际投喂卤虫"
              required
            />
          </label>
          <label>
            冲销操作人
            <input value={operatorName} disabled />
          </label>
          <p className="hint">冲销时刻由系统在提交时自动记录。</p>
          <div className="modal-actions">
            <button type="button" className="btn ghost" onClick={onClose} disabled={submitting}>
              取消
            </button>
            <button type="submit" className="btn danger" disabled={submitting}>
              {submitting ? '提交中…' : '确认冲销'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
