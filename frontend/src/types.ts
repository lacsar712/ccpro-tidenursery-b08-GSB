export type User = {
  id: number
  username: string
  role: string
  display_name: string
}

export type Hatchery = {
  id: number
  name: string
  seawaterSource: string
  notes?: string | null
}

export type Pond = {
  id: number
  hatcheryId: number
  pondCode: string
  species: string
  volumeM3: number
  status: 'stocked' | 'dry' | 'quarantine'
}

export type WaterSample = {
  id: number
  pondId: number
  sampledAt: string
  tempC: number
  salinityPpt: number
  doMgL: number
  ph: number
  notes?: string | null
}

export type FeedEvent = {
  id: number
  pondId: number
  fedAt: string
  feedType: string
  amountKg: number
  operatorName: string
  /** 冲销凭证行：指向被冲销的原投喂编号 */
  reversalOfId?: number | null
  /** 冲销凭证行：冲销原因（至少 6 字） */
  reversalReason?: string | null
  /** 冲销凭证行：冲销时刻 */
  reversedAt?: string | null
  /** 冲销凭证行：冲销操作人 */
  reversedBy?: string | null
  /** 原投喂是否已被冲销 */
  isReversed?: boolean
}

export type DashboardStats = {
  pondTotal: number
  quarantineCount: number
  samplesLast24h: number
  feedKgLast7d: number
}
