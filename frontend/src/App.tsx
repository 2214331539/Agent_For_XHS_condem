import { useEffect, useMemo, useState } from "react";
import {
  App as AntApp,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Radio,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { api } from "./api/client";
import type { Metric, Overview, Post, PostStatus, Product, StylePreset } from "./types";

type View = "dashboard" | "create" | "posts" | "detail" | "metrics" | "analysis";
type StyleMode = "default" | "custom";

interface ProductDraft {
  product_name: string;
  price?: number;
  user_impression: string;
  files: File[];
}

const statusMeta: Record<PostStatus, { label: string; className: string }> = {
  draft: { label: "草稿", className: "tag-yellow" },
  published: { label: "已发表", className: "tag-blue" },
  analyzed: { label: "已分析", className: "tag-green" }
};

function rate(value: number | string | undefined): string {
  const numeric = Number(value ?? 0);
  return `${(numeric * 100).toFixed(2)}%`;
}

function dateText(value?: string): string {
  if (!value) return "未记录";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

export default function App() {
  const { message } = AntApp.useApp();
  const [view, setView] = useState<View>("dashboard");
  const [posts, setPosts] = useState<Post[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [stylePresets, setStylePresets] = useState<StylePreset[]>([]);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const selectedPost = useMemo(() => posts.find((post) => post.id === selectedPostId) ?? null, [posts, selectedPostId]);

  async function refresh() {
    const [postList, overviewData, presets] = await Promise.all([
      api.get<Post[]>("/posts"),
      api.get<Overview>("/analytics/overview"),
      api.get<StylePreset[]>("/style-presets")
    ]);
    setPosts(postList);
    setOverview(overviewData);
    setStylePresets(presets);
  }

  useEffect(() => {
    refresh().catch((error) => message.error(error.message));
  }, []);

  function openPost(post: Post, nextView: View = "detail") {
    setSelectedPostId(post.id);
    setView(nextView);
  }

  async function markPublished(post: Post) {
    await api.post<Post>(`/posts/${post.id}/mark-published`);
    message.success("已标记发布，并创建 7 天数据录入提醒");
    await refresh();
  }

  const content = (() => {
    if (view === "create") {
      return (
        <CreatePost
          presets={stylePresets}
          loading={loading}
          setLoading={setLoading}
          onCreated={async (post) => {
            await refresh();
            setSelectedPostId(post.id);
            setView("detail");
          }}
        />
      );
    }
    if (view === "posts") return <PostsList posts={posts} onOpen={openPost} onMarkPublished={markPublished} />;
    if (view === "detail" && selectedPost) return <PostDetail post={selectedPost} onRefresh={refresh} onMarkPublished={markPublished} />;
    if (view === "metrics" && selectedPost) {
      return (
        <MetricsEntry
          post={selectedPost}
          onSaved={async () => {
            await refresh();
            setView("analysis");
          }}
        />
      );
    }
    if (view === "analysis" && selectedPost) return <AnalysisView post={selectedPost} />;
    return <Dashboard overview={overview} posts={posts} onOpen={openPost} onCreate={() => setView("create")} />;
  })();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-kicker">BYT REVIEW</div>
          <h1>测评工作台</h1>
        </div>
        <nav className="nav-list">
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>首页</button>
          <button className={view === "create" ? "active" : ""} onClick={() => setView("create")}>新建测评</button>
          <button className={view === "posts" ? "active" : ""} onClick={() => setView("posts")}>内容管理</button>
        </nav>
      </aside>
      <main className="main-panel">{content}</main>
    </div>
  );
}

function Dashboard({
  overview,
  posts,
  onOpen,
  onCreate
}: {
  overview: Overview | null;
  posts: Post[];
  onOpen: (post: Post, view?: View) => void;
  onCreate: () => void;
}) {
  const recentPosts = posts.slice(0, 5);
  const bestPost = overview?.best_post;

  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>今天先处理最能推进起号的事项。</h2>
        </div>
        <Button type="primary" onClick={onCreate}>新建测评</Button>
      </header>

      <Row gutter={[16, 16]}>
        <MetricCard title="待发布 Draft" value={overview?.draft_count ?? 0} />
        <MetricCard title="待录入数据" value={overview?.pending_metrics_count ?? 0} />
        <MetricCard title="本周已发布" value={overview?.published_this_week_count ?? 0} />
        <MetricCard title="平均互动率" value={rate(overview?.average_interaction_rate)} />
        <MetricCard title="平均收藏率" value={rate(overview?.average_collect_rate)} />
      </Row>

      <div className="bento-grid">
        <Card className="flat-card wide-card">
          <p className="card-label">今日待办</p>
          <div className="todo-list">
            <p>优先录入已到期帖子的后台数据。</p>
            <p>检查草稿是否已有完整标题、正文和封面文案。</p>
            <p>如果最近 3 天没有发布，准备下一期 3-5 个产品横评。</p>
          </div>
          <Space wrap>
            <Button type="primary" onClick={onCreate}>新建测评</Button>
            <Button onClick={() => posts[0] && onOpen(posts[0], "posts")} disabled={!posts.length}>查看草稿</Button>
          </Space>
        </Card>

        <Card className="flat-card">
          <p className="card-label">表现最佳</p>
          {bestPost ? (
            <div className="best-post">
              <h3>{String(bestPost.title)}</h3>
              <p>浏览 {String(bestPost.views)}，互动率 {rate(String(bestPost.interaction_rate))}</p>
              <p>收藏率 {rate(String(bestPost.collect_rate))}，涨粉 {String(bestPost.followers_gained)}</p>
            </div>
          ) : (
            <p className="muted">录入数据后这里会显示表现最好的帖子。</p>
          )}
        </Card>

        <Card className="flat-card">
          <p className="card-label">下一期提醒</p>
          <p>{overview?.next_suggestion ?? "先创建第一篇测评草稿，跑通发布和数据复盘闭环。"}</p>
        </Card>
      </div>

      <PostsTable posts={recentPosts} onOpen={onOpen} compact />
    </section>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Col xs={24} sm={12} lg={8} xl={4}>
      <Card className="flat-card metric-card">
        <Statistic title={title} value={value} />
      </Card>
    </Col>
  );
}

function CreatePost({
  presets,
  loading,
  setLoading,
  onCreated
}: {
  presets: StylePreset[];
  loading: boolean;
  setLoading: (value: boolean) => void;
  onCreated: (post: Post) => void;
}) {
  const { message } = AntApp.useApp();
  const defaultImagePreset = presets.find((item) => item.preset_type === "image")?.id;
  const defaultCopyPreset = presets.find((item) => item.preset_type === "copy")?.id;
  const [imageMode, setImageMode] = useState<StyleMode>("default");
  const [copyMode, setCopyMode] = useState<StyleMode>("default");
  const [imagePreset, setImagePreset] = useState<string | undefined>(defaultImagePreset);
  const [copyPreset, setCopyPreset] = useState<string | undefined>(defaultCopyPreset);
  const [imageCustomPrompt, setImageCustomPrompt] = useState("");
  const [copyCustomPrompt, setCopyCustomPrompt] = useState("");
  const [products, setProducts] = useState<ProductDraft[]>([{ product_name: "", price: undefined, user_impression: "", files: [] }]);

  useEffect(() => {
    setImagePreset((current) => current ?? defaultImagePreset);
    setCopyPreset((current) => current ?? defaultCopyPreset);
  }, [defaultImagePreset, defaultCopyPreset]);

  async function submit() {
    const validProducts = products.filter((item) => item.product_name.trim() && item.user_impression.trim());
    if (!validProducts.length) {
      message.warning("至少填写一个产品名称和真实感受");
      return;
    }
    if (imageMode === "custom" && !imageCustomPrompt.trim()) {
      message.warning("请输入自定义图片处理风格");
      return;
    }
    if (copyMode === "custom" && !copyCustomPrompt.trim()) {
      message.warning("请输入自定义文案生成风格");
      return;
    }

    setLoading(true);
    try {
      const post = await api.post<Post>("/posts", {
        image_style_preset_id: imageMode === "default" ? imagePreset : undefined,
        image_custom_prompt: imageMode === "custom" ? imageCustomPrompt.trim() : undefined,
        copy_style_preset_id: copyMode === "default" ? copyPreset : undefined,
        copy_custom_prompt: copyMode === "custom" ? copyCustomPrompt.trim() : undefined,
        products: validProducts.map((item, index) => ({
          product_name: item.product_name,
          price: item.price,
          user_impression: item.user_impression,
          sort_order: index
        }))
      });

      await Promise.all(
        validProducts.flatMap((draft, index) =>
          draft.files.map((file) => {
            const formData = new FormData();
            formData.append("file", file);
            return api.post(`/products/${post.products[index].id}/images`, formData);
          })
        )
      );

      const generated = await api.post<Post>(`/posts/${post.id}/generate-copy`);
      message.success("已生成草稿");
      onCreated(generated);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "创建失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">New Draft</p>
          <h2>按产品卡片录入，生成一篇可编辑的小红书测评。</h2>
        </div>
        <Button type="primary" loading={loading} onClick={submit}>生成完整帖子</Button>
      </header>

      <Card className="flat-card">
        <Row gutter={[18, 18]}>
          <Col xs={24} md={12}>
            <label className="field-label">图片处理风格</label>
            <Radio.Group value={imageMode} onChange={(event) => setImageMode(event.target.value)} className="mode-group">
              <Radio.Button value="default">使用系统默认</Radio.Button>
              <Radio.Button value="custom">自定义</Radio.Button>
            </Radio.Group>
            {imageMode === "default" ? (
              <Select value={imagePreset} onChange={setImagePreset} className="full-width">
                {presets.filter((item) => item.preset_type === "image").map((item) => (
                  <Select.Option key={item.id} value={item.id}>{item.name}</Select.Option>
                ))}
              </Select>
            ) : (
              <Input.TextArea
                rows={4}
                value={imageCustomPrompt}
                onChange={(event) => setImageCustomPrompt(event.target.value)}
                placeholder="例如：干净自然光、保留包装文字、3:4 竖图、背景像真实桌面，不要过度商业棚拍。"
              />
            )}
          </Col>
          <Col xs={24} md={12}>
            <label className="field-label">文案生成风格</label>
            <Radio.Group value={copyMode} onChange={(event) => setCopyMode(event.target.value)} className="mode-group">
              <Radio.Button value="default">使用系统默认</Radio.Button>
              <Radio.Button value="custom">自定义</Radio.Button>
            </Radio.Group>
            {copyMode === "default" ? (
              <Select value={copyPreset} onChange={setCopyPreset} className="full-width">
                {presets.filter((item) => item.preset_type === "copy").map((item) => (
                  <Select.Option key={item.id} value={item.id}>{item.name}</Select.Option>
                ))}
              </Select>
            ) : (
              <Input.TextArea
                rows={4}
                value={copyCustomPrompt}
                onChange={(event) => setCopyCustomPrompt(event.target.value)}
                placeholder="例如：像真实朋友聊天，保留轻微吐槽，不要广告腔，先说结论，再说适合和不适合的人。"
              />
            )}
          </Col>
        </Row>
      </Card>

      {products.map((product, index) => (
        <Card className="flat-card product-input-card" key={index}>
          <div className="card-title-row">
            <p className="card-label">产品 {index + 1}</p>
            {products.length > 1 && (
              <Button onClick={() => setProducts((items) => items.filter((_, currentIndex) => currentIndex !== index))}>删除</Button>
            )}
          </div>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <label className="field-label">产品名称</label>
              <Input
                value={product.product_name}
                onChange={(event) =>
                  setProducts((items) =>
                    items.map((item, currentIndex) =>
                      currentIndex === index ? { ...item, product_name: event.target.value } : item
                    )
                  )
                }
              />
            </Col>
            <Col xs={24} md={12}>
              <label className="field-label">价格</label>
              <InputNumber
                value={product.price}
                min={0}
                precision={2}
                className="full-width"
                onChange={(value) =>
                  setProducts((items) =>
                    items.map((item, currentIndex) =>
                      currentIndex === index ? { ...item, price: Number(value ?? 0) } : item
                    )
                  )
                }
              />
            </Col>
            <Col span={24}>
              <label className="field-label">直观感受</label>
              <Input.TextArea
                rows={4}
                value={product.user_impression}
                onChange={(event) =>
                  setProducts((items) =>
                    items.map((item, currentIndex) =>
                      currentIndex === index ? { ...item, user_impression: event.target.value } : item
                    )
                  )
                }
              />
            </Col>
            <Col span={24}>
              <label className="field-label">上传图片</label>
              <input
                className="file-input"
                type="file"
                accept="image/*"
                multiple
                onChange={(event) => {
                  const files = Array.from(event.target.files ?? []);
                  setProducts((items) =>
                    items.map((item, currentIndex) => (currentIndex === index ? { ...item, files } : item))
                  );
                }}
              />
            </Col>
          </Row>
        </Card>
      ))}

      <Button onClick={() => setProducts((items) => [...items, { product_name: "", price: undefined, user_impression: "", files: [] }])}>
        添加产品
      </Button>
    </section>
  );
}

function PostsList({
  posts,
  onOpen,
  onMarkPublished
}: {
  posts: Post[];
  onOpen: (post: Post, view?: View) => void;
  onMarkPublished: (post: Post) => void;
}) {
  const [filter, setFilter] = useState<"all" | PostStatus>("all");
  const filtered = filter === "all" ? posts : posts.filter((post) => post.status === filter);
  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">Content</p>
          <h2>管理草稿、发布记录和复盘状态。</h2>
        </div>
        <Select value={filter} onChange={setFilter} className="filter-select">
          <Select.Option value="all">全部</Select.Option>
          <Select.Option value="draft">草稿</Select.Option>
          <Select.Option value="published">已发表</Select.Option>
          <Select.Option value="analyzed">已分析</Select.Option>
        </Select>
      </header>
      <PostsTable posts={filtered} onOpen={onOpen} onMarkPublished={onMarkPublished} />
    </section>
  );
}

function PostsTable({
  posts,
  onOpen,
  onMarkPublished,
  compact = false
}: {
  posts: Post[];
  onOpen: (post: Post, view?: View) => void;
  onMarkPublished?: (post: Post) => void;
  compact?: boolean;
}) {
  const columns: ColumnsType<Post> = [
    {
      title: "标题",
      dataIndex: "selected_title",
      render: (_, post) => <strong>{post.selected_title || "未命名草稿"}</strong>
    },
    {
      title: "状态",
      dataIndex: "status",
      render: (status: PostStatus) => <Tag className={statusMeta[status].className}>{statusMeta[status].label}</Tag>
    },
    {
      title: "产品",
      render: (_, post) => `${post.products.length} 个`
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      render: dateText
    },
    {
      title: "操作",
      render: (_, post) => (
        <Space wrap>
          <Button onClick={() => onOpen(post, "detail")}>查看</Button>
          {post.status === "draft" && onMarkPublished && <Button onClick={() => onMarkPublished(post)}>已发布</Button>}
          {post.status !== "draft" && <Button onClick={() => onOpen(post, "metrics")}>录入数据</Button>}
          {post.status === "analyzed" && <Button onClick={() => onOpen(post, "analysis")}>复盘</Button>}
        </Space>
      )
    }
  ];
  return <Table rowKey="id" className="flat-table" columns={compact ? columns.slice(0, 4) : columns} dataSource={posts} pagination={false} />;
}

function PostDetail({
  post,
  onRefresh,
  onMarkPublished
}: {
  post: Post;
  onRefresh: () => Promise<void>;
  onMarkPublished: (post: Post) => Promise<void>;
}) {
  const { message } = AntApp.useApp();
  const [modalOpen, setModalOpen] = useState(false);

  async function regenerate() {
    await api.post<Post>(`/posts/${post.id}/regenerate-copy`);
    message.success("文案已重新生成");
    await onRefresh();
  }

  async function copyText(text?: string) {
    await navigator.clipboard.writeText(text ?? "");
    message.success("已复制");
  }

  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">Draft Detail</p>
          <h2>{post.selected_title || "未命名草稿"}</h2>
        </div>
        <Space wrap>
          <Button onClick={regenerate}>重新生成文案</Button>
          {post.status === "draft" && <Button type="primary" onClick={() => setModalOpen(true)}>我已发布</Button>}
        </Space>
      </header>

      <Row gutter={[16, 16]}>
        <MetricCard title="状态" value={statusMeta[post.status].label} />
        <MetricCard title="产品数量" value={post.products.length} />
        <MetricCard title="图片数量" value={post.products.reduce((total, product) => total + product.images.length, 0)} />
        <MetricCard title="发布时间" value={post.published_at ? dateText(post.published_at) : "未发布"} />
      </Row>

      <Tabs
        items={[
          { key: "images", label: "发布图片", children: <ImageGallery products={post.products} /> },
          { key: "products", label: "产品结果", children: <ProductResults products={post.products} /> },
          {
            key: "copy",
            label: "文案编辑",
            children: (
              <Card className="flat-card copy-card">
                <p className="card-label">标题候选</p>
                <ol className="title-options">
                  {post.title_options.map((title) => <li key={title}>{title}</li>)}
                </ol>
                <p className="card-label">最终标题</p>
                <Input value={post.selected_title} readOnly />
                <p className="card-label">正文</p>
                <Input.TextArea rows={12} value={post.content} readOnly />
                <p className="card-label">封面文案</p>
                <Input.TextArea rows={3} value={post.cover_text} readOnly />
                <Space wrap>
                  {post.tags.map((tag) => <Tag className="tag-blue" key={tag}>#{tag}</Tag>)}
                </Space>
                <div className="copy-actions">
                  <Button onClick={() => copyText(post.selected_title)}>复制标题</Button>
                  <Button onClick={() => copyText(post.content)}>复制正文</Button>
                  <Button onClick={() => copyText(post.tags.map((tag) => `#${tag}`).join(" "))}>复制标签</Button>
                </div>
              </Card>
            )
          }
        ]}
      />

      <Modal
        title="确认已经在小红书发布该帖子？"
        open={modalOpen}
        onOk={async () => {
          await onMarkPublished(post);
          setModalOpen(false);
        }}
        onCancel={() => setModalOpen(false)}
      >
        <p>确认后系统会把状态改为已发表，记录发布时间，并创建 7 天后的数据录入提醒。</p>
      </Modal>
    </section>
  );
}

function ImageGallery({ products }: { products: Product[] }) {
  const images = products.flatMap((product) => product.images.map((image) => ({ ...image, productName: product.product_name })));
  if (!images.length) return <Card className="flat-card muted">本篇还没有上传图片。</Card>;
  return (
    <div className="image-grid">
      {images.map((image) => (
        <Card className="flat-card image-card" key={image.id}>
          <img src={image.image_url} alt={image.productName} />
          <div>
            <Tag className={image.image_type === "processed" ? "tag-green" : "tag-yellow"}>{image.image_type}</Tag>
            <p>{image.productName}</p>
            <p className="muted">{image.ai_description || "等待图片 Agent 分析"}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}

function ProductResults({ products }: { products: Product[] }) {
  return (
    <div className="product-result-grid">
      {products.map((product) => (
        <Card className="flat-card" key={product.id}>
          <p className="card-label">{product.product_name}</p>
          <h3>{product.agent_recommendation || "待判断"}</h3>
          <p>{product.agent_summary || product.user_impression}</p>
          <p className="muted">原始感受：{product.user_impression}</p>
        </Card>
      ))}
    </div>
  );
}

function MetricsEntry({ post, onSaved }: { post: Post; onSaved: () => void }) {
  const { message } = AntApp.useApp();
  const [form] = Form.useForm();
  const values = Form.useWatch([], form) ?? {};
  const views = Number(values.views ?? 0);
  const likes = Number(values.likes ?? 0);
  const collects = Number(values.collects ?? 0);
  const comments = Number(values.comments ?? 0);
  const followers = Number(values.followers_gained ?? 0);
  const computed = {
    interaction: views > 0 ? (likes + collects + comments) / views : 0,
    collect: views > 0 ? collects / views : 0,
    follower: views > 0 ? followers / views : 0
  };

  async function submit(analyze: boolean) {
    const payload = await form.validateFields();
    await api.post<Metric>(`/posts/${post.id}/metrics`, { ...payload, analyze });
    message.success(analyze ? "数据已保存并生成复盘" : "数据已保存");
    onSaved();
  }

  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">Metrics</p>
          <h2>{post.selected_title || "未命名帖子"}</h2>
          <p className="muted">发布时间：{dateText(post.published_at)}</p>
        </div>
      </header>
      <Card className="flat-card">
        <Form form={form} layout="vertical" initialValues={{ views: 0, likes: 0, collects: 0, comments: 0, followers_gained: 0 }}>
          <Row gutter={[16, 16]}>
            {["views", "likes", "collects", "comments", "followers_gained"].map((name) => (
              <Col xs={24} md={8} key={name}>
                <Form.Item label={metricLabel(name)} name={name} rules={[{ required: true }]}>
                  <InputNumber min={0} className="full-width" />
                </Form.Item>
              </Col>
            ))}
          </Row>
        </Form>
      </Card>
      <Row gutter={[16, 16]}>
        <MetricCard title="互动率" value={rate(computed.interaction)} />
        <MetricCard title="收藏率" value={rate(computed.collect)} />
        <MetricCard title="转粉率" value={rate(computed.follower)} />
      </Row>
      <Card className="flat-card">
        <p className="card-label">数据质量提示</p>
        <p>{computed.collect >= 0.025 ? "收藏率较高，说明内容有参考价值。" : "收藏率偏低，可以增加明确结论和购买场景。"}</p>
        <p>{computed.follower < 0.005 ? "转粉率偏低，账号记忆点还可以继续强化。" : "转粉表现稳定，可以延续当前内容结构。"}</p>
      </Card>
      <Space wrap>
        <Button onClick={() => submit(false)}>保存数据</Button>
        <Button type="primary" onClick={() => submit(true)}>保存并生成复盘</Button>
      </Space>
    </section>
  );
}

function metricLabel(name: string): string {
  const labels: Record<string, string> = {
    views: "浏览量",
    likes: "点赞数",
    collects: "收藏数",
    comments: "评论数",
    followers_gained: "涨粉数"
  };
  return labels[name];
}

function AnalysisView({ post }: { post: Post }) {
  const [metric, setMetric] = useState<Metric | null>(null);
  const { message } = AntApp.useApp();

  useEffect(() => {
    api.get<Metric>(`/posts/${post.id}/analysis`).then(setMetric).catch((error) => message.error(error.message));
  }, [post.id]);

  const analysis = metric?.analysis_json ?? {};
  return (
    <section className="page-stack reveal">
      <header className="page-header">
        <div>
          <p className="eyebrow">Review</p>
          <h2>{post.selected_title || "复盘分析"}</h2>
        </div>
      </header>
      {metric && (
        <Row gutter={[16, 16]}>
          <MetricCard title="浏览量" value={metric.views} />
          <MetricCard title="互动率" value={rate(metric.interaction_rate)} />
          <MetricCard title="收藏率" value={rate(metric.collect_rate)} />
          <MetricCard title="转粉率" value={rate(metric.follower_rate)} />
        </Row>
      )}
      <Card className="flat-card analysis-card">
        <p className="card-label">AI 复盘结论</p>
        <p>{metric?.analysis_result ?? "还没有生成复盘，请先录入数据并选择保存并生成复盘。"}</p>
      </Card>
      <div className="bento-grid">
        <Card className="flat-card">
          <p className="card-label">标题分析</p>
          <p>{String(analysis.title_advice ?? "标题建议会在复盘后显示。")}</p>
        </Card>
        <Card className="flat-card">
          <p className="card-label">封面建议</p>
          <p>{String(analysis.cover_advice ?? "封面建议会在复盘后显示。")}</p>
        </Card>
        <Card className="flat-card wide-card">
          <p className="card-label">下一期选题</p>
          <Space wrap>
            {Array.isArray(analysis.next_topics)
              ? analysis.next_topics.map((topic) => <Tag className="tag-green" key={String(topic)}>{String(topic)}</Tag>)
              : "暂无建议"}
          </Space>
        </Card>
      </div>
    </section>
  );
}

