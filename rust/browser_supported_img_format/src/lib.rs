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

    pub fn infer(file_name: &str) -> Option<Self> {
        let lower = file_name.to_lowercase();
        if lower.ends_with(".bmp") {
            Some(Self::Bmp)
        } else if lower.ends_with(".png") {
            Some(Self::Png)
        } else if lower.ends_with(".jpg") || lower.ends_with(".jpeg") {
            Some(Self::Jpeg)
        } else if lower.ends_with(".gif") {
            Some(Self::Gif)
        } else if lower.ends_with(".webp") {
            Some(Self::Webp)
        } else if lower.ends_with(".svg") {
            Some(Self::Svg)
        } else {
            None
        }
    }

    /// The value for the `accept` attribute of the HTML `<input type="file" ...>` element.
    ///
    /// See <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>.
    pub fn accept_str() -> &'static str {
        ".bmp,.png,.jpg,.jpeg,.gif,.webp,.svg"
    }
}
