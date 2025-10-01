// Selects the keys of T that are optional
export type OptionalKeys<T> = {
    [K in keyof T]-?: {} extends Pick<T, K> ? K : never
}[keyof T];

export type OptionalProps<T> = Pick<T, OptionalKeys<T>>;

// https://stackoverflow.com/a/61108377/8341513
export type Optional<T, K extends keyof T> = Pick<Partial<T>, K> & Omit<T, K>;

export type IncludesElement<T extends readonly any[], U> =
    T extends [infer Head, ...infer Tail]
    ? [U] extends [Head] ? true
    : IncludesElement<Tail, U>
    : false;

// type TestIncludesElement0 = IncludesElement<[3, 5, 7], 4>;
// type IncludesElement1 = IncludesElement<[3, 5, 7], 5>;

export type IncludesAll<T extends readonly any[], Sub extends readonly any[]> =
    Sub extends [infer Head, ...infer Tail]
    ? IncludesElement<T, Head> extends true
    ? IncludesAll<T, Tail>
    : false
    : true;

// type TestIncludesAll0 = IncludesAll<[3, 5, 7], [4]>;
// type TestIncludesAll1 = IncludesAll<[3, 5, 7], [3, 7]>;
