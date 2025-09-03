# Based on https://github.com/LukeMathWalker/cargo-chef

FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef
WORKDIR /backend

FROM chef AS planner
COPY ./Cargo.toml ./Cargo.toml
COPY ./backend/Cargo.toml ./backend/Cargo.toml
COPY ./backend/src/main.rs ./backend/src/main.rs
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder 
COPY --from=planner /backend/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN cargo chef cook --release --recipe-path recipe.json
# Build application
COPY ./Cargo.toml Cargo.toml
COPY ./backend/ ./backend/
RUN cargo build --release --package backend 

# We do not need the Rust toolchain to run the binary!
FROM debian:bookworm-slim AS runtime
WORKDIR /backend

COPY --from=builder /backend/target/release/backend /usr/local/bin
EXPOSE 3000
ENTRYPOINT ["/usr/local/bin/backend"]
