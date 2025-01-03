using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Duch : MonoBehaviour
{
    private const float moc_skoku = 50f;

    private static Duch instance;

    public static Duch GetInstance()
    {
        return instance;
    }

    public event EventHandler OnDied;
    public event EventHandler OnStartedPlaying;

    private Rigidbody2D duchrigidbody2D;
    private State state;

    private enum State
    {
        WaitingToStart,
        Playing,
        Dead,
    }

    private void Awake()
    {
        instance = this;
        duchrigidbody2D = GetComponent<Rigidbody2D>();
        duchrigidbody2D.bodyType = RigidbodyType2D.Static;
        state = State.WaitingToStart;
    }

    private void Update()
    {
        switch (state)
        {
            default:
            case State.WaitingToStart:
                if (Input.GetKeyDown(KeyCode.Space) || Input.GetMouseButtonDown(0))
                {
                    state = State.Playing;
                    duchrigidbody2D.bodyType = RigidbodyType2D.Dynamic;
                    skok();
                    if (OnStartedPlaying != null) OnStartedPlaying(this, EventArgs.Empty);
                }
                break;
            case State.Playing:
                if (Input.GetKeyDown(KeyCode.Space) || Input.GetMouseButtonDown(0))
                {
                    skok();
                }
                break;
            case State.Dead:
                break;

        }
    }

    private void skok()
    {
        duchrigidbody2D.velocity = Vector2.up * moc_skoku;
    }

    private void OnTriggerEnter2D(Collider2D collider)
    {
        duchrigidbody2D.bodyType = RigidbodyType2D.Static;
        if (OnDied != null) OnDied(this, EventArgs.Empty);
    }
}
