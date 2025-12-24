# Blog System Guide

## Overview

The blog system now supports **structured content blocks** where admins can upload images and place them anywhere within the blog content, mixing text and images in any order.

## Content Structure

Each blog has **content blocks** that can be either:

1. **Text Block** - Contains markdown-formatted text
2. **Image Block** - Contains an uploaded image with optional caption

### Content Block Format

```json
{
  "type": "text",
  "content": "Your markdown text here..."
}
```

```json
{
  "type": "image",
  "url": "/storage/blogs/image-uuid.jpg",
  "alt": "Image description",
  "caption": "Optional caption"
}
```

## API Endpoints

### For Admins (Authentication Required)

#### 1. Upload Image

```
POST /blogs/upload-image
Content-Type: multipart/form-data

Body:
- image: File (image file)

Response:
{
  "url": "/storage/blogs/uuid.jpg",
  "filename": "original-name.jpg"
}
```

#### 2. Create Blog Post

```
POST /blogs/
Content-Type: application/json

Body:
{
  "title": "My Blog Post",
  "subject": "This is the subject/excerpt",
  "content": [
    {
      "type": "text",
      "content": "# Introduction\n\nThis is the first paragraph..."
    },
    {
      "type": "image",
      "url": "/storage/blogs/uuid1.jpg",
      "alt": "Beautiful diving scene",
      "caption": "Diving in the Red Sea"
    },
    {
      "type": "text",
      "content": "More text after the image..."
    },
    {
      "type": "image",
      "url": "/storage/blogs/uuid2.jpg",
      "alt": "Coral reef"
    },
    {
      "type": "text",
      "content": "Final paragraph..."
    }
  ],
  "tags": ["diving", "red-sea", "adventure"]
}

Response:
{
  "id": 1,
  "title": "My Blog Post",
  "subject": "This is the subject/excerpt",
  "content": [...content blocks...],
  "tags": ["diving", "red-sea", "adventure"],
  "created_at": "2025-12-24T20:00:00Z",
  "updated_at": "2025-12-24T20:00:00Z"
}
```

#### 3. Update Blog Post

```
PUT /blogs/{blog_id}
Content-Type: application/json

Body: (all fields optional)
{
  "title": "Updated Title",
  "subject": "Updated subject",
  "content": [...new content blocks...],
  "tags": ["new", "tags"]
}
```

#### 4. Delete Blog Post

```
DELETE /blogs/{blog_id}
```

### For Everyone (No Authentication Required)

#### 1. Get All Blogs (List View)

```
GET /blogs/?skip=0&limit=100

Response:
[
  {
    "id": 1,
    "title": "Blog Title",
    "subject": "Blog subject",
    "tags": ["tag1", "tag2"],
    "created_at": "2025-12-24T20:00:00Z",
    "updated_at": "2025-12-24T20:00:00Z"
  }
]
```

#### 2. Get Blog by ID

```
GET /blogs/id/1

Response: (Full blog with all content blocks)
{
  "id": 1,
  "title": "Blog Title",
  "subject": "Blog subject",
  "content": [...all content blocks...],
  "tags": ["tag1", "tag2"],
  "created_at": "2025-12-24T20:00:00Z",
  "updated_at": "2025-12-24T20:00:00Z"
}
```

#### 3. Get Blog by Title

```
GET /blogs/title/My%20Blog%20Post
```

#### 4. Get Blogs by Tag

```
GET /blogs/tag/diving?skip=0&limit=100
```

#### 5. Search Blogs

```
GET /blogs/search/?q=coral&skip=0&limit=100
```

#### 6. Get All Tags

```
GET /blogs/tags/all

Response:
["diving", "red-sea", "adventure", "coral"]
```

## Frontend Workflow

### Creating a Blog Post (Admin)

1. **Admin writes text** → Creates a text block
2. **Admin clicks "Add Image"** → Frontend uploads image via `/blogs/upload-image`
3. **Backend returns image URL** → Frontend creates an image block with that URL
4. **Admin adds more text** → Creates another text block
5. **Repeat as needed**
6. **Admin clicks "Save"** → Frontend sends all content blocks via `/blogs/` POST

### Example Frontend Flow:

```javascript
// 1. Upload image when admin selects file
const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch("/blogs/upload-image", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  const data = await response.json();
  return data.url; // Returns: "/storage/blogs/uuid.jpg"
};

// 2. Build content array as admin adds blocks
const contentBlocks = [
  { type: "text", content: "# My Title\n\nFirst paragraph..." },
  {
    type: "image",
    url: "/storage/blogs/uuid1.jpg",
    alt: "Description",
    caption: "Caption",
  },
  { type: "text", content: "More text..." },
  { type: "image", url: "/storage/blogs/uuid2.jpg", alt: "Another image" },
  { type: "text", content: "Final text..." },
];

// 3. Create the blog post
const createBlog = async () => {
  const response = await fetch("/blogs/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      title: "My Blog Post",
      subject: "Blog excerpt",
      content: contentBlocks,
      tags: ["diving", "adventure"],
    }),
  });

  return await response.json();
};
```

### Displaying a Blog Post (Frontend)

```javascript
// Fetch blog
const blog = await fetch("/blogs/id/1").then((r) => r.json());

// Render each content block
blog.content.forEach((block) => {
  if (block.type === "text") {
    // Render markdown text
    renderMarkdown(block.content);
  } else if (block.type === "image") {
    // Render image
    renderImage(block.url, block.alt, block.caption);
  }
});
```

## Database Migration

Run the migration to create the blogs table:

```bash
cd /Users/home/WorkSpace/WebApps/NextApp/globaldivers/backend
alembic upgrade head
```

## Key Features

✅ **Image Upload** - Admins upload images, get URLs back
✅ **Structured Content** - Mix text and images in any order
✅ **Markdown Support** - Text blocks support full markdown
✅ **Multiple Images** - Unlimited images anywhere in the blog
✅ **Same View** - Users see content exactly as admin arranged it
✅ **Tags** - Categorize and filter blogs by tags
✅ **Search** - Search by title and subject
✅ **Public Access** - Anyone can read blogs
✅ **Admin Control** - Only admins can create/edit/delete

## Storage

- Images are stored in: `/storage/blogs/`
- Image URLs are relative: `/storage/blogs/filename.jpg`
- Supported formats: JPG, JPEG, PNG, GIF, BMP, WEBP
