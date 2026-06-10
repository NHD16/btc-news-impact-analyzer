import NewsCard from "./NewsCard";

export default function NewsList({ items }) {
  return (
    <div className="list">
      {items.map((it) => (
        <NewsCard key={it.id} item={it} />
      ))}
    </div>
  );
}
