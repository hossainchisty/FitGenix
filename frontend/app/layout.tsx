import "./globals.css";
export const metadata = { title: "Fitssort", description: "Run your whole gym from one place." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
