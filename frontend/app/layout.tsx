import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "NaviCast | Charter Decision Intelligence", description: "Freight forecasting and vessel chartering intelligence for India's East Coast." };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
