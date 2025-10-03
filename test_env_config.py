"""
Test Environment Configuration
Verifies that all API keys are properly configured and working
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from django.conf import settings


def test_env_configuration():
    """
    Test that all environment variables are properly configured
    """
    print("🔧 Testing Environment Configuration")
    print("=" * 40)
    
    # Test Django settings
    print("\n⚙️ Django Configuration:")
    print(f"SECRET_KEY: {'✅ Configured' if settings.SECRET_KEY else '❌ Missing'}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # Test Bitnob API
    print("\n💰 Bitnob API Configuration:")
    bitnob_key = getattr(settings, 'BITNOB_API_KEY', '')
    bitnob_url = getattr(settings, 'BITNOB_BASE_URL', '')
    print(f"API Key: {'✅ Configured' if bitnob_key else '❌ Missing'}")
    print(f"Base URL: {bitnob_url}")
    
    # Test MavaPay API
    print("\n💳 MavaPay API Configuration:")
    mavapay_key = getattr(settings, 'MAVAPAY_API_KEY', '')
    mavapay_url = getattr(settings, 'MAVAPAY_BASE_URL', '')
    print(f"API Key: {'✅ Configured' if mavapay_key else '❌ Missing'}")
    print(f"Base URL: {mavapay_url}")
    
    # Test Gemini API
    print("\n🤖 Gemini API Configuration:")
    gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
    print(f"API Key: {'✅ Configured' if gemini_key else '❌ Missing'}")
    
    # Test WhatsApp API
    print("\n📱 WhatsApp API Configuration:")
    whatsapp_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    whatsapp_phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    whatsapp_verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
    print(f"Access Token: {'✅ Configured' if whatsapp_token else '❌ Missing'}")
    print(f"Phone Number ID: {'✅ Configured' if whatsapp_phone_id else '❌ Missing'}")
    print(f"Verify Token: {'✅ Configured' if whatsapp_verify_token else '❌ Missing'}")
    
    # Test Redis/Celery
    print("\n🔄 Redis/Celery Configuration:")
    redis_url = getattr(settings, 'REDIS_URL', '')
    print(f"Redis URL: {'✅ Configured' if redis_url else '❌ Missing'}")
    
    # Summary
    print("\n📊 Configuration Summary:")
    print("=" * 25)
    
    configs = [
        ("Django", bool(settings.SECRET_KEY)),
        ("Bitnob API", bool(bitnob_key)),
        ("MavaPay API", bool(mavapay_key)),
        ("Gemini API", bool(gemini_key)),
        ("WhatsApp API", bool(whatsapp_token and whatsapp_phone_id)),
        ("Redis", bool(redis_url))
    ]
    
    configured_count = sum(1 for _, configured in configs if configured)
    total_count = len(configs)
    
    for config_name, configured in configs:
        status = "✅ Configured" if configured else "❌ Missing"
        print(f"{config_name}: {status}")
    
    print(f"\n🎯 Total: {configured_count}/{total_count} configured")
    
    if configured_count == total_count:
        print("🚀 All configurations are ready!")
    else:
        print("🔧 Some configurations are missing - check your .env file")
    
    return configured_count == total_count


def show_env_file_template():
    """
    Show the complete .env file template
    """
    print("\n📝 Complete .env File Template:")
    print("=" * 35)
    print("""
# Django Configuration
SECRET_KEY=django-insecure-z(8p6+1=15nbdrtkyk6=da0h)g7b8yqj$x4e0!p0&0#dq2)$p5
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Bitnob API Configuration
BITNOB_API_KEY=your_bitnob_api_key_here
BITNOB_BASE_URL=https://api.bitnob.com

# MavaPay API Configuration
MAVAPAY_API_KEY=your_mavapay_api_key_here
MAVAPAY_BASE_URL=https://api.mavapay.co

# Gemini AI API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token_here

# Database Configuration (for production)
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
""")


if __name__ == "__main__":
    is_configured = test_env_configuration()
    show_env_file_template()
    
    if not is_configured:
        print("\n💡 Next Steps:")
        print("1. Create a .env file in your project root")
        print("2. Copy the template above")
        print("3. Replace the placeholder values with your actual API keys")
        print("4. Run this test again to verify configuration")
