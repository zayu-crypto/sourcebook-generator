# Design System - Sourcebook Generator

## Direction
**Personality:** Warmth & Approachability  
**Foundation:** Warm slate (educational, inviting)  
**Depth:** Subtle shadows (soft, accessible feel)  
**Purpose:** Educational tool - should feel encouraging and professional

---

## Tokens

### Color Palette
**Primary Colors:**
- Brand: #667eea (thoughtful blue-purple)
- Accent: #764ba2 (depth and focus)

**Semantic Colors:**
- Success: #10b981 (confidence, action)
- Warning: #f59e0b (attention)
- Error: #ef4444 (problems)
- Info: #3b82f6 (guidance)

**Neutral Scale:**
- Foreground Primary: #1f2937 (main text)
- Foreground Secondary: #6b7280 (supporting text)
- Foreground Tertiary: #9ca3af (metadata)
- Foreground Muted: #d1d5db (disabled, placeholder)
- Surface Base: #ffffff (card backgrounds)
- Surface Secondary: #f9fafb (subtle background)
- Surface Tertiary: #f3f4f6 (grouped sections)
- Border Default: rgba(0, 0, 0, 0.08)
- Border Subtle: rgba(0, 0, 0, 0.05)

### Spacing System
**Base Unit:** 8px  
**Scale:** 4, 8, 12, 16, 20, 24, 32, 40

### Border Radius
- Small: 6px (buttons, inputs)
- Medium: 8px (cards)
- Large: 12px (modals)

### Shadows
**Depth: Subtle shadows**
- Subtle: `0 1px 2px rgba(0, 0, 0, 0.05)`
- Medium: `0 4px 6px rgba(0, 0, 0, 0.07)`
- Elevated: `0 10px 15px rgba(0, 0, 0, 0.1)`

### Typography
- **Heading:** system fonts, weight 700
- **Body:** system fonts, weight 400
- **Label:** system fonts, weight 600

---

## Patterns

### Button Primary
- Height: 44px
- Padding: 12px 24px
- Radius: 6px
- Font: 1em, weight 600
- Background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
- Hover: transform -2px, shadow medium
- Transition: all 0.3s

### Button Secondary
- Height: 44px
- Padding: 12px 24px
- Radius: 6px
- Border: 1px solid #e5e7eb
- Background: white
- Hover: border-color #667eea, shadow subtle

### Card
- Border: 1px solid #e5e7eb
- Padding: 20px
- Radius: 8px
- Background: white
- Shadow: subtle
- Hover: border-color #667eea, shadow medium
- Transition: all 0.3s

### Input
- Height: 40px
- Padding: 12px 16px
- Radius: 6px
- Border: 1px solid #e5e7eb
- Font: 1em
- Focus: border-color #667eea, box-shadow 0 0 0 3px rgba(102, 126, 234, 0.1)

---

## Principles

**Warmth**: Generous spacing, rounded corners, soft shadows - welcomes users who are new to development

**Clarity**: Strong hierarchy, clear button states, obvious affordances - reduces cognitive load

**Consistency**: Token reuse across all components - predictability builds confidence

**Progression**: 10 cards displayed in grid - easy to scan, easy to select

---

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Gradient brand colors | Adds energy to primary actions, reflects educational nature | 2026-02-13 |
| Subtle shadows over harsh borders | Approachable feel, not technical or dense | 2026-02-13 |
| Generous spacing (8px base) | Research: more space = less intimidating, easier to read | 2026-02-13 |
| Card-based layout | Encourages incremental choices, feels less overwhelming | 2026-02-13 |
| Blue-purple palette | Intellectual, trustworthy, educational (think: universities) | 2026-02-13 |

