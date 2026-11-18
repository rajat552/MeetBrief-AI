export interface ManualMeetingRequest {
  company_name: string;
  attendee_name: string;
  attendee_email?: string;
  attendee_role?: string;
  meeting_datetime: string;
  meeting_title?: string;
  meeting_goal?: string;
}

export interface ResearchFinding {
  category: 'company_background' | 'attendee_dossier' | 'news' | 'launches' | 'hiring' | 'undated';
  title: string;
  summary: string;
  source_url: string;
  source_title: string;
  published_date?: string;
  freshness_days_ago?: number;
  reliability_tier: number;
  matched_passage?: string;
}

export interface VerifiedClaim {
  claim: string;
  verification_status: 'VERIFIED_PRIMARY' | 'REPORTED_SECONDARY' | 'UNVERIFIED' | 'CONFLICTED';
  source_url: string;
  source_title: string;
  source_passage?: string;
  source_date?: string;
  alignment_score: number;
  confidence_score: number;
  conflict_notes?: string;
}

export interface CompanyProfile {
  company_name: string;
  business_model: string;
  core_products: string[];
  target_market: string;
  competitive_moat: string;
  key_competitors: string[];
}

export interface AttendeeDossier {
  name: string;
  verified_title?: string;
  current_company: string;
  career_history: string[];
  public_stances_and_quotes: string[];
  likely_agenda?: string;
  communication_hook?: string;
}

export interface OnePageBriefing {
  briefing_id: string;
  target_company: string;
  target_attendee: string;
  meeting_datetime: string;
  meeting_goal?: string;
  card1_executive_snapshot: string;
  card2_company_profile: CompanyProfile;
  card3_attendee_dossier: AttendeeDossier;
  card4_recent_30d_signals: ResearchFinding[];
  card5_discussion_hooks: string[];
  card6_risk_blindspots: string[];
  verified_claims: VerifiedClaim[];
  undated_signals: ResearchFinding[];
  aggregate_confidence: number;
  inference_route: 'bifrost_gateway' | 'fallback_direct';
  generated_at: string;
}

export interface GatewayStatusEvent {
  mode: 'bifrost_gateway' | 'fallback_direct';
  endpoint: string;
  reason?: string;
  available_models?: string[];
  primary_model?: string;
  fallback_model?: string;
  virtual_key_active?: boolean;
}

export interface StageUpdateEvent {
  stage: string;
  status: 'active' | 'done';
  description: string;
}

export interface SourceDiscoveredEvent {
  url: string;
  title: string;
  category: string;
  tier: number;
  published_date?: string;
}

export interface ClaimsVerifiedEvent {
  total: number;
  verified_count: number;
  reported_count: number;
  conflicted_count: number;
}
