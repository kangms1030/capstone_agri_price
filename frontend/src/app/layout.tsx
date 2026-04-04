import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Agri-Insight | 배추 도매가격 예측",
  description:
    "KAMIS 도매가격 데이터 + Chronos TSFM + Gemini AI를 활용한 배추 가격 14일 예측 대시보드",
  keywords: ["배추 가격", "농산물 예측", "KAMIS", "도매가격", "AI 예측"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
