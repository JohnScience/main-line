use mnln_core_items::Timestamp;

pub fn now() -> Timestamp {
    let now = chrono::Utc::now();
    let timestamp = now.timestamp_millis();
    Timestamp(timestamp as u64)
}

pub fn time_from_now(duration: chrono::Duration) -> Timestamp {
    let later = chrono::Utc::now() + duration;
    let timestamp = later.timestamp_millis();
    Timestamp(timestamp as u64)
}
