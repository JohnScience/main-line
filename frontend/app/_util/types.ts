// Selects the keys of T that are optional
export type OptionalKeys<T> = {
    [K in keyof T]-?: {} extends Pick<T, K> ? K : never
}[keyof T];

export type OptionalProps<T> = Pick<T, OptionalKeys<T>>;

// https://stackoverflow.com/a/61108377/8341513
export type Optional<T, K extends keyof T> = Pick<Partial<T>, K> & Omit<T, K>;
