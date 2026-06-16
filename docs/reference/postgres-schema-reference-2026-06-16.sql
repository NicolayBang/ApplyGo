-- ApplyPilot PostgreSQL schema reference snapshot
-- Generated from local Docker PostgreSQL on 2026-06-16.
-- Reference-only artifact. Authoritative schema remains Alembic migrations plus repository contracts.

--
-- PostgreSQL database dump
--


-- Dumped from database version 16.14 (Debian 16.14-1.pgdg13+1)
-- Dumped by pg_dump version 16.14 (Debian 16.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: application_packet_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application_packet_reviews (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    decision character varying(32) NOT NULL,
    reviewed_by character varying(64) NOT NULL,
    source character varying(32) NOT NULL,
    packet_text text,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_application_packet_reviews_decision_m2 CHECK (((decision)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying, 'changes_requested'::character varying])::text[]))),
    CONSTRAINT ck_application_packet_reviews_source_m2 CHECK (((source)::text = 'dashboard'::text))
);


--
-- Name: applications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.applications (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    state character varying(64) DEFAULT 'ApplicationCreated'::character varying NOT NULL,
    automation_mode character varying(32) DEFAULT 'manual'::character varying NOT NULL,
    fit_score integer,
    confidence character varying(16),
    recommendation character varying(32),
    score_reasons jsonb,
    score_risks jsonb,
    missing_data jsonb,
    red_flags jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_applications_automation_mode_m1 CHECK (((automation_mode)::text = ANY ((ARRAY['manual'::character varying, 'dry_run'::character varying, 'semi_auto'::character varying, 'full_auto'::character varying])::text[]))),
    CONSTRAINT ck_applications_state_m1 CHECK (((state)::text = ANY ((ARRAY['ApplicationCreated'::character varying, 'Draft'::character varying, 'ReadyForReview'::character varying, 'Approved'::character varying, 'Submitted'::character varying, 'Rejected'::character varying, 'Archived'::character varying])::text[])))
);


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id uuid NOT NULL,
    name character varying(256) NOT NULL,
    normalized_name character varying(256) NOT NULL,
    domain character varying(256),
    normalized_domain character varying(256),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_companies_name_not_blank_m3 CHECK (((name)::text <> ''::text)),
    CONSTRAINT ck_companies_normalized_name_not_blank_m3 CHECK (((normalized_name)::text <> ''::text))
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    doc_type character varying(64) NOT NULL,
    content text,
    content_json jsonb,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: email_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_threads (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    external_thread_id character varying(256),
    subject character varying(512),
    direction character varying(16) DEFAULT 'inbound'::character varying NOT NULL,
    classification character varying(64),
    raw_body text,
    draft_reply text,
    sent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_email_threads_direction_m1 CHECK (((direction)::text = ANY ((ARRAY['inbound'::character varying, 'outbound'::character varying])::text[])))
);


--
-- Name: event_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_log (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    event_type character varying(128) NOT NULL,
    actor character varying(64) DEFAULT 'system'::character varying NOT NULL,
    from_state character varying(64),
    to_state character varying(64),
    payload jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: executor_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.executor_actions (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    idempotency_key character varying(256) NOT NULL,
    action_type character varying(64) NOT NULL,
    execution_mode character varying(16) NOT NULL,
    status character varying(32) DEFAULT 'queued'::character varying NOT NULL,
    payload jsonb,
    result jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    request_id uuid NOT NULL,
    worker character varying(32) NOT NULL,
    requested_by character varying(64) NOT NULL,
    requested_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_executor_actions_execution_mode_m1 CHECK (((execution_mode)::text = ANY ((ARRAY['dry_run'::character varying, 'execute'::character varying])::text[]))),
    CONSTRAINT ck_executor_actions_status_m1 CHECK (((status)::text = ANY ((ARRAY['planned'::character varying, 'queued'::character varying, 'completed'::character varying, 'failed'::character varying, 'blocked'::character varying, 'not_implemented'::character varying])::text[]))),
    CONSTRAINT ck_executor_actions_worker_m1 CHECK (((worker)::text = ANY ((ARRAY['email'::character varying, 'browser'::character varying, 'documents'::character varying])::text[])))
);


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.jobs (
    id uuid NOT NULL,
    source_url character varying(2048),
    raw_text text,
    title character varying(512),
    company_source_text character varying(256),
    location character varying(256),
    remote_ok boolean DEFAULT false NOT NULL,
    job_type character varying(64),
    ats_type character varying(64),
    salary_raw character varying(256),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    company_id uuid NOT NULL
);


--
-- Name: policy_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.policy_decisions (
    id uuid NOT NULL,
    application_id uuid NOT NULL,
    action_type character varying(64) NOT NULL,
    mode character varying(32) NOT NULL,
    allowed boolean NOT NULL,
    reasons jsonb,
    risks jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    decision character varying(16) DEFAULT 'review'::character varying NOT NULL,
    required_overrides jsonb,
    CONSTRAINT ck_policy_decisions_decision_m1 CHECK (((decision)::text = ANY ((ARRAY['allow'::character varying, 'deny'::character varying, 'review'::character varying])::text[]))),
    CONSTRAINT ck_policy_decisions_mode_m1 CHECK (((mode)::text = ANY ((ARRAY['manual'::character varying, 'dry_run'::character varying, 'semi_auto'::character varying, 'full_auto'::character varying])::text[])))
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: application_packet_reviews application_packet_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_packet_reviews
    ADD CONSTRAINT application_packet_reviews_pkey PRIMARY KEY (id);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: email_threads email_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_threads
    ADD CONSTRAINT email_threads_pkey PRIMARY KEY (id);


--
-- Name: event_log event_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_pkey PRIMARY KEY (id);


--
-- Name: executor_actions executor_actions_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executor_actions
    ADD CONSTRAINT executor_actions_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: executor_actions executor_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executor_actions
    ADD CONSTRAINT executor_actions_pkey PRIMARY KEY (id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: policy_decisions policy_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_decisions
    ADD CONSTRAINT policy_decisions_pkey PRIMARY KEY (id);


--
-- Name: executor_actions uq_executor_actions_request_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executor_actions
    ADD CONSTRAINT uq_executor_actions_request_id UNIQUE (request_id);


--
-- Name: ix_application_packet_reviews_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_application_packet_reviews_application_id ON public.application_packet_reviews USING btree (application_id);


--
-- Name: ix_application_packet_reviews_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_application_packet_reviews_created_at ON public.application_packet_reviews USING btree (created_at);


--
-- Name: ix_applications_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_job_id ON public.applications USING btree (job_id);


--
-- Name: ix_applications_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_applications_state ON public.applications USING btree (state);


--
-- Name: ix_companies_normalized_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_normalized_domain ON public.companies USING btree (normalized_domain);


--
-- Name: ix_companies_normalized_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_normalized_name ON public.companies USING btree (normalized_name);


--
-- Name: ix_documents_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_documents_application_id ON public.documents USING btree (application_id);


--
-- Name: ix_email_threads_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_threads_application_id ON public.email_threads USING btree (application_id);


--
-- Name: ix_event_log_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_log_application_id ON public.event_log USING btree (application_id);


--
-- Name: ix_event_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_log_created_at ON public.event_log USING btree (created_at);


--
-- Name: ix_event_log_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_log_event_type ON public.event_log USING btree (event_type);


--
-- Name: ix_executor_actions_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_executor_actions_application_id ON public.executor_actions USING btree (application_id);


--
-- Name: ix_executor_actions_idempotency_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_executor_actions_idempotency_key ON public.executor_actions USING btree (idempotency_key);


--
-- Name: ix_executor_actions_request_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_executor_actions_request_id ON public.executor_actions USING btree (request_id);


--
-- Name: ix_jobs_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_company_id ON public.jobs USING btree (company_id);


--
-- Name: ix_jobs_company_source_text; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_jobs_company_source_text ON public.jobs USING btree (company_source_text);


--
-- Name: ix_policy_decisions_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_policy_decisions_application_id ON public.policy_decisions USING btree (application_id);


--
-- Name: uq_companies_normalized_domain_m3; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_companies_normalized_domain_m3 ON public.companies USING btree (normalized_domain) WHERE (normalized_domain IS NOT NULL);


--
-- Name: uq_companies_normalized_name_without_domain_m3; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_companies_normalized_name_without_domain_m3 ON public.companies USING btree (normalized_name) WHERE (normalized_domain IS NULL);


--
-- Name: application_packet_reviews application_packet_reviews_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_packet_reviews
    ADD CONSTRAINT application_packet_reviews_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id);


--
-- Name: applications applications_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: documents documents_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id) ON DELETE CASCADE;


--
-- Name: email_threads email_threads_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_threads
    ADD CONSTRAINT email_threads_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id) ON DELETE CASCADE;


--
-- Name: event_log event_log_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id);


--
-- Name: executor_actions executor_actions_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executor_actions
    ADD CONSTRAINT executor_actions_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id);


--
-- Name: jobs jobs_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: policy_decisions policy_decisions_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_decisions
    ADD CONSTRAINT policy_decisions_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id);


--
-- PostgreSQL database dump complete
--


