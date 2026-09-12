import { AuthProvider } from "../components/AuthProvider";
import "./globals.css";

export const metadata = {
  title: "CrewLink",
  description: "Leadership announcements for a union local",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
