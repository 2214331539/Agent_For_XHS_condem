export type PostStatus = "draft" | "published" | "analyzed";

export interface StylePreset {
  id: string;
  preset_type: "image" | "copy" | string;
  name: string;
  description?: string;
  prompt_template: string;
  default_params: Record<string, unknown>;
}

export interface CardImage {
  id: string;
  card_id: string;
  image_type: string;
  image_url: string;
  sort_order: number;
  final_sort_order?: number;
  is_selected_for_post: boolean;
  ai_description?: string;
}

export interface Product {
  id: string;
  post_id: string;
  product_name: string;
  price?: string | number;
  user_impression: string;
  sort_order: number;
  agent_summary?: string;
  agent_recommendation?: string;
  agent_detail?: Record<string, unknown>;
  images: CardImage[];
}

export interface Post {
  id: string;
  status: PostStatus;
  selected_title?: string;
  title_options: string[];
  content?: string;
  cover_text?: string;
  tags: string[];
  comment_guide?: string;
  recommendation_level?: string;
  published_at?: string;
  analyzed_at?: string;
  created_at: string;
  updated_at: string;
  products: Product[];
}

export interface Metric {
  id: string;
  post_id: string;
  views: number;
  likes: number;
  collects: number;
  comments: number;
  followers_gained: number;
  interaction_rate: string | number;
  collect_rate: string | number;
  follower_rate: string | number;
  analysis_result?: string;
  analysis_json: Record<string, unknown>;
  recorded_at: string;
}

export interface Overview {
  draft_count: number;
  pending_metrics_count: number;
  published_this_week_count: number;
  average_interaction_rate: number;
  average_collect_rate: number;
  best_post: Record<string, unknown> | null;
  next_suggestion: string;
}

