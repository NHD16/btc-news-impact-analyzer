import NewsCard from "./NewsCard";

export default function NewsList({ items, newItemIds }) {
  const newIds = new Set(newItemIds || []);
  return (
    <div className="list">
      {items.map((it) => (
        <NewsCard key={it.id} item={it} isNew={newIds.has(it.id)} />
      ))}
    </div>
  );
}
