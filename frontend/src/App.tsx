import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layout/AppLayout";
import { BoardPage } from "@/pages/BoardPage";
import { BookmarksPage } from "@/pages/BookmarksPage";
import { CategoriesPage } from "@/pages/CategoriesPage";
import { CategoryDetailPage } from "@/pages/CategoryDetailPage";
import { HomePage } from "@/pages/HomePage";
import { SharePage } from "@/pages/SharePage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="categories" element={<CategoriesPage />} />
        <Route path="categories/:name" element={<CategoryDetailPage />} />
        <Route path="bookmarks" element={<BookmarksPage />} />
        <Route path="board" element={<BoardPage />} />
        <Route path="share" element={<SharePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
