import Link from "next/link";
export default function AuthSide() {
  return <div className="authside"><Link href="/" className="logo" style={{ marginBottom: "auto", textDecoration: "none" }}><i />Fitssort</Link><blockquote>I finally know who is about to leave before they do.</blockquote><p className="hint" style={{ color: "#9bb0a6" }}>Gym owner, Dhaka</p></div>;
}
