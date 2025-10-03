from django.db import models
import uuid


class ChatSession(models.Model):
    """
    Track AI chatbot conversations with users
    """
    user = models.ForeignKey('core.BitzappUser', on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.phone_number} - Session {self.session_id}"


class ChatMessage(models.Model):
    """
    Individual messages in chat sessions
    """
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
        ('system', 'System Message'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    tokens_used = models.IntegerField(default=0, help_text="Number of tokens used for AI response")
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.session.user.phone_number} - {self.message_type} - {self.content[:50]}..."


class AIKnowledge(models.Model):
    """
    Store AI knowledge base entries for Bitcoin and Bitzapp
    """
    CATEGORIES = [
        ('bitcoin_basics', 'Bitcoin Basics'),
        ('bitzapp_features', 'Bitzapp Features'),
        ('security', 'Security'),
        ('troubleshooting', 'Troubleshooting'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    content = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords for search")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "AI Knowledge"
        verbose_name_plural = "AI Knowledge Base"
        ordering = ['category', 'title']
    
    def __str__(self):
        return f"{self.category} - {self.title}"
