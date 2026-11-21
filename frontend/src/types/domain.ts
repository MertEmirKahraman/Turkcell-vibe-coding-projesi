export interface Shop {
  id: number
  name: string
  address: string | null
  latitude: number | null
  longitude: number | null
  is_active: boolean
  distance_km?: number | null
  product_count?: number
}

export interface Product {
  id: number
  name: string
  description: string | null
  price: number
}

export interface ShopDetail extends Shop {
  menu: Product[]
}

export interface QRCodePayload {
  order_id: string
  user_id: string
  shop_id: string
  created_at: string
  signature: string
}

export interface OrderItem {
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  customization: {
    size: string
    sugar_level: number
    milk_preference: string
    extra_shots: number
  }
}

export interface Order {
  id: number
  user_id: number
  shop_id: number
  shop_name: string
  status: string
  total_amount: number
  created_at: string
  updated_at: string
  items: OrderItem[]
  qr_code: QRCodePayload | null
}

export interface AuthResult {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: number
    phone_number: string
    full_name: string | null
    role: string
    profile_completed: boolean
  }
}

export interface SubscriptionPlan {
  plan_type: 'STARTER' | 'PREMIUM' | 'UNLIMITED'
  name: string
  monthly_price: number
  monthly_credits: number | null
  guest_credits: number
  priority: boolean
  validity_days: number
}

export interface ActiveSubscription {
  active: boolean
  subscription: {
    plan_type: SubscriptionPlan['plan_type']
    plan_name: string
    remaining_credits: number | null
    expires_at: string
  } | null
}
