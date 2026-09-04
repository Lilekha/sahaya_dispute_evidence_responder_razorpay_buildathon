# SaHaYa ML Data Dictionary v6

Primary target: dispute_outcome (won/lost) on contested disputes only.

Decisive evidence per reason code:
  MERCHANDISE_NOT_RECEIVED     -> delivery_confirmation
  SERVICE_NOT_RENDERED         -> service_record
  RECURRING_BILLING_DISPUTE    -> cancellation_record
  CREDIT_NOT_PROCESSED         -> invoice
  DUPLICATE_TRANSACTION        -> invoice
  MERCHANDISE_NOT_AS_DESCRIBED -> customer_communication (all terms halved)
  UNAUTHORIZED_TRANSACTION     -> otp_3ds_status on transaction

Outcome logit terms:
  +1.9 decisive present quality>=0.80
  +1.1 decisive present quality 0.55-0.79
  -2.1 decisive missing
  +2.0 UNAUTHORIZED 3DS passed
  -1.4 UNAUTHORIZED 3DS failed
  +0.45 each other required doc present
  -0.75 each other required doc missing
  +0.9*(mean_quality-0.7) quality term
  -0.32*(log10(amount)-3.4) amount term
  -0.30*min(prior_disputes,4) customer term
  Noise: Gaussian sigma=0.85

Evidence slots:
  physical_delivery  : order_confirmation, invoice, customer_communication,
                       shipping_label, tracking_number, delivery_confirmation
  digital_service    : order_confirmation, invoice, customer_communication,
                       access_log, service_record, cancellation_record
  membership_service : same as digital_service
  booking_service    : same as digital_service

Forbidden columns (never in any table):
  transactions : merchant_archetype, fulfillment_type, industry,
                 chargeback_created, chargeback_outcome, dispute_type
  disputes     : should_contest, recommended_action, simulated_win_probability,
                 expected_recovery, expected_cost, expected_net_value, contestable,
                 dispute_status, chargeback_outcome, evidence_strength,
                 evidence_completeness, merchant_response_submitted
