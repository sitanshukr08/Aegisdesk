# External Services

The `app/services` directory contains modules bridging AegisDesk with external third-party infrastructure.

## 🔐 Auth Service
`auth_service.py` handles the issuance and verification of JWT (JSON Web Tokens). It pairs with the FastAPI `OAuth2PasswordBearer` scheme to authenticate users accessing the streaming endpoints.

## 📡 Webhook Service
`webhook_service.py` is responsible for pushing state out of the graph. When the LangGraph pipeline reaches a terminal failure state (e.g., maximum recursion reached, or a severe security fault), this service triggers a webhook escalation to ServiceNow or PagerDuty, attaching the full chat history and diagnostic graph.

## 👁️ Vision Service
`vision_service.py` handles multimodal inputs. When an IT operator pastes a screenshot of a Blue Screen of Death (BSOD) or an error dialog, this service parses the image, runs OCR/Vision-Language models, and injects the extracted error codes straight into the LangGraph state matrix.
