pub enum BrowserSupportedImgFormat {
    Bmp,
    Png,
    Jpeg,
    Gif,
    Webp,
    Svg,
}

impl BrowserSupportedImgFormat {
    pub fn ext(&self) -> &'static str {
        match self {
            Self::Bmp => "bmp",
            Self::Png => "png",
            Self::Jpeg => "jpg",
            Self::Gif => "gif",
            Self::Webp => "webp",
            Self::Svg => "svg",
            // Consider Avif
        }
    }

    /// The value for the `accept` attribute of the HTML `<input type="file" ...>` element.
    ///
    /// See <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>.
    pub fn accept_str() -> &'static str {
        ".bmp,.png,.jpg,.jpeg,.gif,.webp,.svg"
    }
}
