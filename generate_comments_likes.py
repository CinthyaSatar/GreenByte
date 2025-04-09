"""
Script to generate random comments and likes for posts in the database.
"""
import random
from datetime import datetime, timedelta

from greenbyte import db, createApp
from greenbyte.models import User, Post, Comment
from greenbyte.utils.timezone import now_in_timezone

# Constants for generation
NUM_COMMENTS_PER_POST = 5  # Average number of comments per post
MAX_REPLIES_PER_COMMENT = 3  # Maximum number of replies per comment
LIKE_PROBABILITY = 0.7  # Probability that a user will like a post (70%)

# Comment templates
comment_templates = [
    "Great post! I love your {plant_name}. They look so healthy!",
    "Thanks for sharing! I've been thinking about growing {plant_name} in my garden too.",
    "Beautiful garden! How often do you water your {plant_name}?",
    "I've had similar issues with {pest}. Have you tried using {solution}?",
    "Your {garden_name} looks amazing! How long have you been gardening?",
    "I'm new to gardening and this is really helpful. Do you have any tips for beginners?",
    "I've been growing {plant_name} for years and never thought to try {action}. Great idea!",
    "What kind of soil do you use for your {plant_name}?",
    "Have you had any issues with pests in your {garden_name}?",
    "The layout of your garden is so inspiring! I might try something similar.",
    "Do you use any organic fertilizers for your {plant_name}?",
    "How do you deal with {garden_problem} in your garden?",
    "I love the variety of plants in your garden! Where do you get your seeds?",
    "Your {plant_name} are thriving! What's your secret?",
    "This is exactly what I needed to read today. My {plant_name} have been struggling.",
]

reply_templates = [
    "Thanks for your comment! I water my {plant_name} about twice a week.",
    "I've been gardening for about 3 years now. It's been a wonderful journey!",
    "I use a mix of compost and potting soil for my {plant_name}.",
    "Yes, I've had issues with {pest} too. I use neem oil and it works great!",
    "I get my seeds from a local nursery, but sometimes I order online too.",
    "For beginners, I'd recommend starting with herbs or {plant_name}. They're pretty forgiving!",
    "I've found that {action} really helps with growth and yield.",
    "I've been dealing with {garden_problem} by using {solution}.",
    "Thank you! I've put a lot of work into my {garden_name}.",
    "I use organic fertilizer every two weeks during the growing season.",
    "I've had my {garden_name} for about 2 years now.",
    "I'd be happy to share some cuttings if you're local!",
    "The key is consistent care and paying attention to what your plants need.",
    "I've learned so much from this community. Everyone is so helpful!",
    "Let me know if you try it out! I'd love to see your results.",
]

# Lists for template placeholders
plant_names = ["tomatoes", "peppers", "basil", "lettuce", "carrots", "cucumbers", "zucchini", "strawberries", "blueberries", "roses", "sunflowers", "lavender", "mint", "rosemary", "thyme"]
garden_names = ["vegetable garden", "herb garden", "flower bed", "container garden", "raised beds", "indoor garden", "vertical garden", "hydroponic setup", "greenhouse", "community garden plot"]
pests = ["aphids", "slugs", "caterpillars", "whiteflies", "spider mites", "fungus gnats", "Japanese beetles", "squash bugs", "tomato hornworms", "cabbage worms"]
solutions = ["neem oil", "diatomaceous earth", "companion planting", "insecticidal soap", "beneficial insects", "row covers", "hand-picking", "organic sprays", "sticky traps", "crop rotation"]
garden_problems = ["weeds", "poor drainage", "compacted soil", "nutrient deficiency", "overwatering", "underwatering", "too much sun", "not enough sun", "frost damage", "heat stress"]
actions = ["mulching", "pruning", "fertilizing", "composting", "crop rotation", "companion planting", "succession planting", "vertical growing", "trellising", "deep watering"]

def generate_comments_and_likes():
    """Generate random comments and likes for posts"""
    app = createApp()
    with app.app_context():
        # Get all users and posts
        users = User.query.all()
        posts = Post.query.all()

        if not users or not posts:
            print("No users or posts found in the database. Please run database_generator.py and generate_posts.py first.")
            return

        print(f"Found {len(users)} users and {len(posts)} posts")

        # Generate likes for posts
        like_count = 0
        for post in posts:
            # For each user, decide if they will like this post
            for user in users:
                # Skip if the user is the author (can't like their own post)
                if user.id == post.user_id:
                    continue

                # 70% chance of liking the post
                if random.random() < LIKE_PROBABILITY:
                    # Add the like if it doesn't already exist
                    if not post.is_liked_by(user):
                        post.like(user)
                        like_count += 1

        db.session.commit()
        print(f"Generated {like_count} likes across {len(posts)} posts")

        # Generate comments for posts
        comment_count = 0
        reply_count = 0

        for post in posts:
            # Determine how many comments this post will have (random between 0 and 2*NUM_COMMENTS_PER_POST)
            num_comments = random.randint(0, 2 * NUM_COMMENTS_PER_POST)

            # Generate top-level comments
            top_level_comments = []
            for _ in range(num_comments):
                # Select a random user (not the author)
                potential_commenters = [u for u in users if u.id != post.user_id]
                if not potential_commenters:
                    continue

                commenter = random.choice(potential_commenters)

                # Select a random comment template and fill in the placeholders
                template = random.choice(comment_templates)
                content = template.format(
                    plant_name=random.choice(plant_names),
                    garden_name=random.choice(garden_names),
                    pest=random.choice(pests),
                    solution=random.choice(solutions),
                    garden_problem=random.choice(garden_problems),
                    action=random.choice(actions)
                )

                # Create a random date between the post date and now
                post_date = post.date_posted
                now = now_in_timezone()

                # Ensure both dates are timezone-aware or naive
                if post_date.tzinfo is None and now.tzinfo is not None:
                    # Make post_date timezone-aware
                    from datetime import timezone
                    post_date = post_date.replace(tzinfo=timezone.utc)

                # Calculate time difference
                time_diff = max(1, int((now - post_date).total_seconds()))
                comment_date = post_date + timedelta(seconds=random.randint(0, time_diff))

                # Create the comment
                comment = Comment(
                    content=content,
                    post_id=post.id,
                    user_id=commenter.id,
                    date_posted=comment_date
                )

                db.session.add(comment)
                db.session.flush()  # Get the comment ID
                top_level_comments.append(comment)
                comment_count += 1

            # Generate replies to some of the top-level comments
            for comment in top_level_comments:
                # Determine if this comment will have replies (50% chance)
                if random.random() < 0.5:
                    # Determine how many replies (1 to MAX_REPLIES_PER_COMMENT)
                    num_replies = random.randint(1, MAX_REPLIES_PER_COMMENT)

                    for _ in range(num_replies):
                        # The post author has a 50% chance of replying, otherwise it's a random user
                        if random.random() < 0.5:
                            replier = User.query.get(post.user_id)
                        else:
                            potential_repliers = [u for u in users if u.id != comment.user_id]
                            if not potential_repliers:
                                continue
                            replier = random.choice(potential_repliers)

                        # Select a random reply template and fill in the placeholders
                        template = random.choice(reply_templates)
                        content = template.format(
                            plant_name=random.choice(plant_names),
                            garden_name=random.choice(garden_names),
                            pest=random.choice(pests),
                            solution=random.choice(solutions),
                            garden_problem=random.choice(garden_problems),
                            action=random.choice(actions)
                        )

                        # Create a random date between the comment date and now
                        comment_date = comment.date_posted
                        now = now_in_timezone()

                        # Ensure both dates are timezone-aware or naive
                        if comment_date.tzinfo is None and now.tzinfo is not None:
                            # Make comment_date timezone-aware
                            from datetime import timezone
                            comment_date = comment_date.replace(tzinfo=timezone.utc)

                        # Calculate time difference
                        time_diff = max(1, int((now - comment_date).total_seconds()))
                        reply_date = comment_date + timedelta(seconds=random.randint(0, time_diff))

                        # Create the reply
                        reply = Comment(
                            content=content,
                            post_id=post.id,
                            user_id=replier.id,
                            parent_id=comment.id,
                            date_posted=reply_date
                        )

                        db.session.add(reply)
                        reply_count += 1

        # Commit all changes
        db.session.commit()
        print(f"Generated {comment_count} comments and {reply_count} replies across {len(posts)} posts")

if __name__ == "__main__":
    generate_comments_and_likes()
