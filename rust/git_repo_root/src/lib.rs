use std::process::{Command, Stdio};

fn check_git_installation() -> anyhow::Result<()> {
    let status = Command::new("git")
        .arg("--version")
        .stdout(Stdio::null()) // Redirect stdout to null
        .stderr(Stdio::null())
        .status()?;
    if !status.success() {
        anyhow::bail!("Git is not installed or not found in PATH.");
    }
    Ok(())
}

pub fn git_repo_root() -> anyhow::Result<String> {
    check_git_installation()?;

    let output = Command::new("git")
        .args(&["rev-parse", "--show-toplevel"])
        .output()?;
    if !output.status.success() {
        anyhow::bail!("Failed to get git repository root.");
    }
    let mut path = String::from_utf8(output.stdout)?;

    // Technically, the output should always end with a newline, but just in case
    if path.ends_with('\n') {
        path.pop();
    }

    Ok(path)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let repo_root = git_repo_root().unwrap();

        println!("Git repository root: {}", repo_root);
    }
}
